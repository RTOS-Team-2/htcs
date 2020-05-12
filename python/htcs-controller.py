import time
import logging
import threading
import mqtt_connector
from car import Car, DetailedCarTracker
from enum import Enum
from HTCSPythonUtil import config


logger = logging.getLogger(__name__)
lock = threading.Lock()
INTERVAL_MS = 100


class Command(Enum):
    MAINTAIN_SPEED = '0'
    ACCELERATE = '1'
    BRAKE = '2'
    CHANGE_LANE = '3'
    TERMINATE = '4'


class AccelerationState(Enum):
    MAINTAINING_SPEED = 0
    ACCELERATING = 1
    BRAKING = 2


def give_command(car: Car, command: Command):
    topic = config["base_topic"] + "/" + str(car.id) + "/command"
    logger.error(f"{command.name} sent to car with id {car.id}")
    mqtt_connector.client_1.publish(topic, command.value, config["quality_of_service"])


def control_traffic():
    logger.error("iteration start")
    # for car in local_cars.get_all():
    #     logger.warning(f"car id = {car.id} distance = {car.distance_taken}, lane = {car.lane}")
    for car in local_cars.get_all():
        # in the traffic lane we slow down if we are over our preferred speed. in this case, we also do nothing else
        if car.speed > car.specs.preferred_speed and car.effective_lane() == 1:
            give_command(car, Command.BRAKE)
            continue

        # if we are too close to the one ahead us
        car_directly_ahead = local_cars.car_directly_ahead_in_effective_lane(car, car.effective_lane())
        # logger.warning(f"car id = {car.id}")
        # if car_directly_ahead_if_keep_lane is not None:
        #     logger.warning(f"car ahead id = {car_directly_ahead_if_keep_lane.id}")
        if car_directly_ahead is not None \
                and car.acceleration_state != AccelerationState.BRAKING \
                and car_directly_ahead.distance_taken - car.distance_taken < min(50, 2 * car.follow_distance()) \
                and car.speed > car_directly_ahead.speed:
            decide_brake_or_overtake(car)
            continue
        # if we aren't too close we accelerate if we are far enough, otherwise try to overtake
        # this is needed, so cars do not get stuck behind each other, and also, who has already switched lanes,
        # into express, should accelerate
        if car.speed < car.specs.preferred_speed:
            if car.acceleration_state == AccelerationState.BRAKING \
                    and car_directly_ahead is not None \
                    and car_directly_ahead.distance_taken - car.distance_taken > min(100, car.follow_distance() * 3):
                give_command(car, Command.MAINTAIN_SPEED)
            if car.acceleration_state != AccelerationState.ACCELERATING \
                    and (car_directly_ahead is None
                         or car_directly_ahead.distance_taken - car.distance_taken > min(100, car.follow_distance() * 5)
                         or car_directly_ahead.speed > car.specs.preferred_speed):
                if car.speed < 5:
                    logger.error(f"id = {car.id}, "
                                 f"speed={car.speed}, "
                                 f"distance taken = {car.distance_taken}, "
                                 f"accstate={car.acceleration_state}, "
                                 f"acc={car.specs.acceleration}, "
                                 f"fdist={car.follow_distance()}")
                give_command(car, Command.ACCELERATE)

        # try to get back to traffic lane
        if car.lane == 5 and local_cars.can_return_to_traffic_lane(car):
            give_command(car, Command.CHANGE_LANE)
        # try to get into traffic lane
        elif car.lane == 0 and local_cars.can_merge_in(car):
            give_command(car, Command.CHANGE_LANE)


def decide_brake_or_overtake(car: Car):
    # in the express lane we brake by all means
    if car.effective_lane() == 2:
        give_command(car, Command.BRAKE)
    # in the merge lane we merge in if possible, otherwise brake
    elif car.effective_lane() == 0:
        if local_cars.can_merge_in(car):
            give_command(car, Command.CHANGE_LANE)
            give_command(car, Command.ACCELERATE)
        else:
            give_command(car, Command.BRAKE)
    # in the traffic lane we overtake. This function checks, that we have to be IN the traffic lane (not in 1 or 4)
    else:
        if local_cars.can_overtake(car):
            give_command(car, Command.CHANGE_LANE)
            give_command(car, Command.ACCELERATE)
        else:
            give_command(car, Command.BRAKE)


if __name__ == "__main__":
    local_cars = DetailedCarTracker()
    mqtt_connector.setup_connector(local_cars)
    time.sleep(1)
    interval_sec = INTERVAL_MS / 1000
    while True:
        time_start = time.time()
        control_traffic()
        logger.info(f"controlling took {time.time() - time_start} seconds")
        remaining_sec = time_start + interval_sec - time.time()
        if remaining_sec <= 0:
            logger.warning("Controller is feeling overloaded, it has no time to sleep! :(")
        else:
            time.sleep(remaining_sec)
