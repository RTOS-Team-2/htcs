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
        self.last_archive_time = time.time()
        self.archive_start_id = 1
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def archive_logs(self):
        _now = time.time()

        if self.last_archive_time > (_now - (ARCHIVE_LOG_ZIP_SIZE + 1) * VEHICLE_MAX_LIFE_EXPECTANCY):
            return False

        start_idx = self.archive_start_id
        end_idx = self.archive_start_id + ARCHIVE_LOG_ZIP_SIZE
        zip_file_name = current_logs_dir + "/archive/" + str(start_idx) + "-" + str(end_idx - 1) + ".zip"
        with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            for i in range(start_idx, end_idx):
                base_name = "htcs_vehicle-" + str(i) + "-" + now_str + ".log"
                full_name = os.path.join(current_logs_dir, base_name)
                zf.write(full_name, base_name)
                os.remove(full_name)

        self.archive_start_id = end_idx
        self.last_archive_time = _now
        return True

    def bury_zombies(self):
        self.running_children = [child for child in self.running_children if child[0].poll() is None]

    def kill_too_old(self):
        first_child = self.running_children[0]
        if elapsed >= first_child[1] + VEHICLE_MAX_LIFE_EXPECTANCY:
            self.running_children.pop(0)
            first_child[0].terminate()
            return first_child[0]
        return None

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
        for _process, _, _, _ in self.running_children:
            _process.terminate()


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
        logger.info(f"Generated vehicle client_id: {client_id} process_id: {process.pid} "
                    f"next vehicle in {sleep_time:.3f} seconds")

        time.sleep(sleep_time)

        elapsed += sleep_time

        grave_digger.bury_zombies()
        killed = grave_digger.kill_too_old()
        if killed is not None:
            logger.info(f"Killed too old child process_id: {killed.pid}")
        if grave_digger.archive_logs():
            logger.info("Archived logs")
