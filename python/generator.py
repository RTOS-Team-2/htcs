import os
import time
import signal
import random
import logging
import pathlib
import zipfile
import datetime
import subprocess
from HTCSPythonUtil import config
from typing import List, Tuple

logger = logging.getLogger("Vehicle_generator")
logger.setLevel(level=logging.DEBUG)

repo_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
executable_name_windows = repo_root_dir + "/htcs-vehicle/Debug/htcs-vehicle.exe"
executable_name_linux = repo_root_dir + "/htcs-vehicle/build/htcs_vehicle"
logs_dir = repo_root_dir + "/python/logs"

GENERATE_TIME_INTERVAL_MIN = 4
GENERATE_TIME_INTERVAL_WIDTH = 1
PREF_SPEED_INTERVAL_MIN = 50
PREF_SPEED_INTERVAL_WIDTH = 110
MAX_SPEED_INTERVAL_MIN = 100
MAX_SPEED_INTERVAL_WIDTH = 180
ACCELERATION_INTERVAL_MIN = 3
ACCELERATION_INTERVAL_WIDTH = 11
BRAKING_POWER_INTERVAL_MIN = 3
BRAKING_POWER_INTERVAL_WIDTH = 11
SIZE_INTERVAL_MIN = 3
SIZE_INTERVAL_WIDTH = 3

VEHICLE_MAX_LIFE_EXPECTANCY = 300  # seconds
ARCHIVE_LOG_ZIP_SIZE = 50


class GraveDigger:
    kill_now = False

    def __init__(self):
        self.running_children: List[Tuple[subprocess.Popen, int, int, str]] = []
        self.ready_to_archive: List[Tuple[int, str]] = []
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def archive_logs(self):
        if len(self.ready_to_archive) == ARCHIVE_LOG_ZIP_SIZE:
            client_no_first = self.ready_to_archive[0][0]
            client_no_last = self.ready_to_archive[len(self.ready_to_archive) - 1][0]
            zip_file_name = current_logs_dir + "/archive/" + str(client_no_first) + "-" + str(client_no_last) + ".zip"
            with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
                for _client_id, _log_file in self.ready_to_archive:
                    base_name = os.path.basename(os.path.normpath(_log_file))
                    zf.write(_log_file, base_name)
                    os.remove(_log_file)
            self.ready_to_archive.clear()
            return True
        return False

    def kill_too_old(self):
        first_child, first_child_created, client_no, _log_file_name = self.running_children[0]
        if elapsed >= first_child_created + VEHICLE_MAX_LIFE_EXPECTANCY:
            self.running_children.pop(0)
            self.ready_to_archive.append((client_no, _log_file_name))
            first_child.terminate()
            return first_child
        return None

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
        for child, _, _, _ in self.running_children:
            child.terminate()


if __name__ == "__main__":
    if os.name is not 'nt':
        os.putenv("LD_LIBRARY_PATH", os.getenv("HOME") + "/Eclipse-Paho-MQTT-C-1.3.1-Linux/lib")

    grave_digger = GraveDigger()
    now = datetime.datetime.now()
    now_str = now.strftime('%Y%m%d%H%M%S')
    current_logs_dir = logs_dir + "/generation-" + now_str
    pathlib.Path(current_logs_dir + "/archive").mkdir(exist_ok=True, parents=True)
    logger.info("Starting generation, output dir: " + current_logs_dir)
    elapsed = 0
    counter = 0
    while not grave_digger.kill_now:
        counter = counter + 1
        sleep_time = random.random() * GENERATE_TIME_INTERVAL_WIDTH + GENERATE_TIME_INTERVAL_MIN
        client_id = str(counter) + "-" + now_str
        params_string = f"--address {config['address']} " \
                        f"--username {config['username']} " \
                        f"--password {config['password']} " \
                        f"--clientId {client_id} " \
                        f"--topic {config['base_topic']} " \
                        f"--preferredSpeed {random.random() * PREF_SPEED_INTERVAL_WIDTH + PREF_SPEED_INTERVAL_MIN} " \
                        f"--maxSpeed {random.random() * MAX_SPEED_INTERVAL_WIDTH + MAX_SPEED_INTERVAL_MIN} " \
                        f"--acceleration {random.random() * ACCELERATION_INTERVAL_WIDTH + ACCELERATION_INTERVAL_MIN} " \
                        f"--brakingPower {random.random() * BRAKING_POWER_INTERVAL_WIDTH + BRAKING_POWER_INTERVAL_MIN} " \
                        f"--size {random.random() * SIZE_INTERVAL_WIDTH + SIZE_INTERVAL_MIN}"

        log_file_name = current_logs_dir + "/htcs_vehicle-" + client_id + ".log"
        log_file = open(log_file_name, "w")
        if os.name == 'nt':
            process = subprocess.Popen(f'"{executable_name_windows}" ' + params_string,
                                       shell=True, stdout=log_file, stderr=log_file)
        else:
            process = subprocess.Popen(executable=executable_name_linux, args=params_string.split(' '),
                                       shell=True, stdout=log_file, stderr=log_file)

        grave_digger.running_children.append((process, elapsed, counter, log_file_name))
        logger.info("Generated vehicle client_id: " + client_id + " process_id: " + str(process.pid)
                     + ", next vehicle in " + str(sleep_time) + " seconds")

        time.sleep(sleep_time)

        elapsed += sleep_time

        killed = grave_digger.kill_too_old()
        if killed is not None:
            logger.info("Killed too old child process_id: " + str(killed.pid))
        if grave_digger.archive_logs():
            logger.info("Archived logs")
