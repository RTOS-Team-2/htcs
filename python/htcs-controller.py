import time
import logging
import mqtt_connector
from car import Car, DetailedCarTracker
from enum import Enum
from HTCSPythonUtil import config


logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)

INTERVAL_MS = 1000


class Command(Enum):
    MAINTAIN_SPEED = 0
    ACCELERATE = 1
    BRAKE = 2
    CHANGE_LANE = 3
    TERMINATE = 4


def give_command(car, command):
    qos = config["quality_of_service"]
    topic = config["base_topic"] + "/" + str(car.id) + "/command"
    logger.debug(topic)
    message = command.value
    mqtt_connector.client_1.publish(topic, message, qos)


def print_all_distances(all_cars):
    for car in all_cars:
        print(f"{car.id}: {car.distance_taken}m")


def control_traffic():
    cars_list = list(local_cars.values())
    cars_list.sort(key=Car.get_distance_taken)
#    cars_list.sort(key=lambda c: c.distance_taken)
#    print_all_distances(car_list)
    cars_priority_list = get_cars_needing_control(cars_list, False)
    control_lane_change(cars_priority_list)
    control_follow_distance(cars_list)


def get_cars_needing_control(all_cars, order_by_priority=True):
    cars_needing_control = []
    for car in all_cars:
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
            give_command(car, Command.CHANGE_LANE)


def control_follow_distance(cars_list):
    return
    prev_car = None
    for car in cars_list:
        if not prev_car:
            return
        if should_slow_down(perv_car, car):
            match_speed(prev_car, car)
            pass
        prev_car = car


def match_speed(prev_car, car):
    pass


def should_slow_down(perv_car, car):
    pass
    
    
#HELP include car.size in calculations
def is_too_close(prev_car, car):
    # greedy = 
    return prev_car.distance_taken + car.get_follow_distance() > car.distance_taken


def is_in_merge_lane(car):
    return car.lane == 0


def is_in_preferred_speed(car):
    return car.speed == car.specs.preferred_speed


def can_change_lane(changing_car, all_cars):
#    if changing_car.lane = 
    # TODO implement condition for changing lane
    return True


if __name__ == "__main__":
    local_cars = DetailedCarTracker()
    mqtt_connector.setup_connector(local_cars)
    time.sleep(1)
    interval_sec = INTERVAL_MS / 1000
    while True:
        time_start = time.time()
        control_traffic()
        remaining_sec = time_start + interval_sec - time.time()
        if remaining_sec <= 0:
            logger.warning("Controller is feeling overloaded, it has no time to sleep! :(")
        else:
            time.sleep(remaining_sec)
