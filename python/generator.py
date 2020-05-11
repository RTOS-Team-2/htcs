import os
import time
import signal
import random
import logging
import pathlib
import zipfile
import datetime
import subprocess
import mqtt_connector
from car import CarSpecs
from typing import List, Tuple, Dict
from HTCSPythonUtil import config

logger = logging.getLogger("Vehicle_generator")

repo_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
executable_name_windows = repo_root_dir + "/htcs-vehicle/Debug/htcs-vehicle.exe"
executable_name_linux = repo_root_dir + "/htcs-vehicle/build/htcs_vehicle"
logs_dir = repo_root_dir + "/python/logs"

GENERATE_TIME_INTERVAL_MIN = 4
GENERATE_TIME_INTERVAL_WIDTH = 1
PREF_SPEED_INTERVAL_MIN = 80
PREF_SPEED_INTERVAL_WIDTH = 110
MAX_SPEED_INTERVAL_MIN = 120
MAX_SPEED_INTERVAL_WIDTH = 180
ACCELERATION_INTERVAL_MIN = 3
ACCELERATION_INTERVAL_WIDTH = 14
BRAKING_POWER_INTERVAL_MIN = 3
BRAKING_POWER_INTERVAL_WIDTH = 14
SIZE_INTERVAL_MIN = 3.5
SIZE_INTERVAL_WIDTH = 5.5

ARCHIVE_LOG_ZIP_SIZE = 50


class GraveDigger:
    kill_now = False

    def __init__(self):
        self.running_children: Dict[str, subprocess.Popen] = {}
        self.last_archive_time = time.time()
        # list of tuples of client_id and client number
        self.ready_to_archive: List[Tuple[str, int]] = []
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def add_to_ready_to_archive(self, _client_id: str):
        self.running_children.pop(_client_id)
        self.ready_to_archive.append((_client_id, int(_client_id.split('-')[0])))
        if len(self.ready_to_archive) >= ARCHIVE_LOG_ZIP_SIZE:
            # sort by client number
            self.ready_to_archive.sort(key=lambda x: x[1])
            _, client_numbers = zip(*self.ready_to_archive)
            # first x client numbers where x is ARCHIVE_LOG_ZIP_SIZE
            lst = client_numbers[:ARCHIVE_LOG_ZIP_SIZE + 1]
            # check if this list of client numbers contains sequential elements
            if lst == list(range(min(lst), max(lst) + 1)):
                # we want to archive together logs of sequential clients
                archive_logs(lst[0])

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
        for _process in self.running_children.values():
            _process.terminate()


def archive_logs(start_idx):
    end_idx = start_idx + ARCHIVE_LOG_ZIP_SIZE
    zip_file_name = os.path.join(current_logs_dir, "archive", str(start_idx), "-", str(end_idx - 1), ".zip")
    with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for i in range(start_idx, end_idx):
            base_name = os.path.join("htcs_vehicle-", str(i), "-", now_str, ".log")
            full_name = os.path.join(current_logs_dir, base_name)
            zf.write(full_name, base_name)
            os.remove(full_name)
    logger.info("Archived logs")


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


def on_terminate(client, userdata, message):
    _client_id = message.payload.decode("utf-8")
    logger.debug(f"Obituary received for car: {_client_id}")
    grave_digger.add_to_ready_to_archive(_client_id)


if __name__ == "__main__":
    # the generator is only interested in obituary messages
    mqtt_connector.setup_connector(on_terminate=on_terminate, _state_client_pool_size=0)
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
        grave_digger.running_children[client_id] = process

        sleep_time = random.random() * GENERATE_TIME_INTERVAL_WIDTH + GENERATE_TIME_INTERVAL_MIN
        logger.info(f"Generated vehicle client_id: {client_id} process_id: {process.pid}"
                    f", next vehicle in {sleep_time:.3f} seconds")
        time.sleep(sleep_time)
        elapsed += sleep_time
