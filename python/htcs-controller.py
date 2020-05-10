from HTCSPythonUtil import config, local_cars
from pprint import pprint
from enum import Enum
import time
import copy
import logging
import mqtt_connector

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)

INTERVAL_MS = 1000


class Command(Enum):
    MAINTAIN_SPEED = 0
    ACCELERATE = 1
    BRAKE = 2
    CHANGE_LANE = 3
    TERMINATE = 4


def control_traffic():
    # Make a copy because local_cars can get modified durring calculations
    all_cars_snapshot = copy.deepcopy(local_cars)
#    sorted_cars = sort-
    #TODO - implement logic for cars already being controlled
    currently_controlled_cars = "TODO"
    #TODO
    #cars_priority_list = cars_needing_control(all_cars_snapshot,True)
    cars_priority_list = cars_needing_control(all_cars_snapshot,False)
    control_lane_change(cars_priority_list)


def cars_needing_control(all_cars, order_by_priority=True):
    # FIXME: erre a pycharm dob warningot: shadows name from outer scope. ugyanaz a változó neve mint a függvénynek
    cars_needing_control = []
    for car in all_cars.values():
        if is_in_merge_lane(car) or not is_in_preferred_speed(car):
            cars_needing_control.append(car)
    if not order_by_priority:
        return cars_needing_control
    else:
        #TODO - order by priority
        cars_by_priority = []
        return cars_by_priority


def control_lane_change(cars_priority_list):
    for car in cars_priority_list:
        if is_in_merge_lane(car) and can_change_lane(car, cars_priority_list):
            give_command(car,Command.CHANGE_LANE)


def give_command(car,command):
    qos = config["quality_of_service"]
    topic = config["base_topic"] + "/" + str(car.id) + "/command"
    logger.debug(topic)
    message = command.value
    mqtt_connector.client_1.publish(topic, message, qos)

            
def is_in_merge_lane(car):
    return car.lane == 0


def is_in_preferred_speed(car):
    return car.speed == car.specs.preferred_speed


def can_change_lane(changing_car, all_cars):
    # TODO implement condition for changing lane
    return True


if __name__ == "__main__":
    mqtt_connector.setup_connector()
    
    interval_sec = INTERVAL_MS / 1000
    while True:
        time_start = time.time()
        control_traffic()
        remaining_sec = time_start + interval_sec - time.time()
        if remaining_sec <= 0:
            logger.warning("Controller is feeling overloaded, it has no time to sleep! :(")
        else:
            time.sleep(remaining_sec)
