import os
import time
import signal
import random
import logging
import pathlib
import zipfile
import datetime
import subprocess
from car import CarSpecs
from typing import List, Tuple
from HTCSPythonUtil import config

logger = logging.getLogger(__name__)

repo_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
executable_name_windows = repo_root_dir + "/htcs-vehicle/Debug/htcs-vehicle.exe"
executable_name_linux = repo_root_dir + "/htcs-vehicle/build/htcs_vehicle"
logs_dir = repo_root_dir + "/python/logs"

GENERATE_TIME_INTERVAL_MIN = 2
GENERATE_TIME_INTERVAL_WIDTH = 1
PREF_SPEED_INTERVAL_MIN = 80
PREF_SPEED_INTERVAL_WIDTH = 110
MAX_SPEED_INTERVAL_MIN = 120
MAX_SPEED_INTERVAL_WIDTH = 180
ACCELERATION_INTERVAL_MIN = 5
ACCELERATION_INTERVAL_WIDTH = 11
BRAKING_POWER_INTERVAL_MIN = 1.5
BRAKING_POWER_INTERVAL_WIDTH = 5
SIZE_INTERVAL_MIN = 3.5
SIZE_INTERVAL_WIDTH = 5.5

VEHICLE_MAX_LIFE_EXPECTANCY = 600  # seconds
ARCHIVE_LOG_ZIP_SIZE = 50

ARCHIVE_INTERVAL = VEHICLE_MAX_LIFE_EXPECTANCY +\
                   (ARCHIVE_LOG_ZIP_SIZE + 1) * (GENERATE_TIME_INTERVAL_MIN + GENERATE_TIME_INTERVAL_WIDTH)


class GraveDigger:
    kill_now = False

    def __init__(self):
        # a list of tuples of processes and their creation time since the start of the program
        self.running_children: List[Tuple[subprocess.Popen, int]] = []
        self.last_archive_time = time.time()
        self.archive_start_id = 1
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def archive_logs(self):
        _now = time.time()

        if self.last_archive_time > (_now - ARCHIVE_INTERVAL):
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

    def kill_too_old(self):
        first_child = self.running_children[0]
        if first_child[0].poll() is not None:
            self.running_children.pop(0)
            logger.debug(f"First child was terminated by an outer source: {first_child[0].pid}")
            return None
        if elapsed >= first_child[1] + VEHICLE_MAX_LIFE_EXPECTANCY:
            self.running_children.pop(0)
            first_child[0].terminate()
            return first_child[0]
        return None

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
        for _process, _, in self.running_children:
            _process.terminate()


def generate_random_specs():
    pref_speed = random.random() * PREF_SPEED_INTERVAL_WIDTH + PREF_SPEED_INTERVAL_MIN
    max_speed = max(pref_speed, random.random() * MAX_SPEED_INTERVAL_WIDTH + MAX_SPEED_INTERVAL_MIN)
    acceleration = random.random() * ACCELERATION_INTERVAL_WIDTH + ACCELERATION_INTERVAL_MIN
    brake = random.random() * BRAKING_POWER_INTERVAL_WIDTH + BRAKING_POWER_INTERVAL_MIN
    size = random.random() * SIZE_INTERVAL_WIDTH + SIZE_INTERVAL_MIN
    # input has to be a tuple
    return CarSpecs((pref_speed, max_speed, acceleration, brake, size))


def generate_params_string(current_id):
    specs = generate_random_specs()
    entry_dist = 0
    if random.random() > 0.70:
        entry_dist = config["entry_2_meter"]
        entry_lane = 0
        start_speed = 50
    else:
        lane_random = random.random()
        if lane_random > 0.75:
            entry_lane = 5
            start_speed = specs.preferred_speed
        elif lane_random > 0.5:
            entry_lane = 2
            start_speed = specs.preferred_speed
        else:
            entry_dist = config["entry_1_meter"]
            entry_lane = 0
            start_speed = 50
    long_string = f"--address {config['address']} " \
                  f"--username {config['username']} " \
                  f"--password {config['password']} " \
                  f"--clientId {current_id} " \
                  f"--topic {config['base_topic']} " \
                  f"--startingLane {entry_lane} " \
                  f"--startingDistance {entry_dist} " \
                  f"--startingSpeed {start_speed} " \
                  f"--preferredSpeed {specs.preferred_speed} " \
                  f"--maxSpeed {specs.max_speed} " \
                  f"--acceleration {specs.acceleration} " \
                  f"--brakingPower {specs.braking_power} " \
                  f"--size {specs.size}"
    return long_string


if __name__ == "__main__":
    if os.name is not 'nt' and os.getenv("HOME"):
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
        client_id = str(counter) + "-" + now_str
        log_file_name = current_logs_dir + "/htcs_vehicle-" + client_id + ".log"
        log_file = open(log_file_name, "w")
        params_string = generate_params_string(client_id)

        if os.name == 'nt':
            process = subprocess.Popen(f'"{executable_name_windows}" ' + params_string,
                                       shell=True, stdout=log_file, stderr=log_file)
        else:
            process = subprocess.Popen(executable=executable_name_linux, args=params_string.split(' '),
                                       shell=True, stdout=log_file, stderr=log_file)
        grave_digger.running_children.append((process, elapsed))

        sleep_time = random.random() * GENERATE_TIME_INTERVAL_WIDTH + GENERATE_TIME_INTERVAL_MIN
        logger.info(f"Generated vehicle client_id: {client_id} process_id: {process.pid}"
                    f", next vehicle in {sleep_time:.3f} seconds")
        time.sleep(sleep_time)
        elapsed += sleep_time

        killed = grave_digger.kill_too_old()
        if killed is not None:
            logger.info(f"Terminated the oldest child, process_id: {killed.pid}")
        if grave_digger.archive_logs():
            logger.info("Archived logs")
