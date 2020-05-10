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

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

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
        self.ready_to_archive: List[Tuple[subprocess.Popen, int, int, str]] = []
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def archive_logs(self):
        _now = time.time()
        externally_terminated_children = [child for child in self.running_children
                                          if child[0].poll() is not None and
                                          child not in self.ready_to_archive]
        if len(externally_terminated_children) > 0:
            logging.debug(f"Found externally terminated children: {externally_terminated_children}")
            for child in externally_terminated_children:
                self.ready_to_archive.append(child)
                self.running_children.remove(child)
            self.ready_to_archive.sort(key=lambda child: child[2])

        if len(self.ready_to_archive) < ARCHIVE_LOG_ZIP_SIZE:
            logging.debug(f"Not enough logs to be archived just yet: {len(self.ready_to_archive)}")
            return False

        logging.debug(f"Archiving logs: {self.ready_to_archive}")
        _now_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        zip_file_name = current_logs_dir + "/archive/archive-" + _now_str + ".zip"
        with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            for child in self.ready_to_archive:
                base_name = os.path.basename(os.path.normpath(child[3]))
                zf.write(child[3], base_name)
                os.remove(child[3])

        self.ready_to_archive.clear()
        return True

    def kill_too_old(self):
        first_child = self.running_children[0]
        if elapsed >= first_child[1] + VEHICLE_MAX_LIFE_EXPECTANCY:
            self.running_children.pop(0)
            self.ready_to_archive.append(first_child)
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
    logging.info("Starting generation, output dir: " + current_logs_dir)
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
        logging.info(f"Generated vehicle client_id: {client_id} process_id: {process.pid} "
                     f"next vehicle in {sleep_time:.3f} seconds")

        time.sleep(sleep_time)

        elapsed += sleep_time

        killed = grave_digger.kill_too_old()
        if killed is not None:
            logging.info(f"Killed too old child process_id: {killed.pid}")
        if grave_digger.archive_logs():
            logging.info("Archived logs")
