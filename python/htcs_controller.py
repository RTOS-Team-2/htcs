import time
import logging
import threading
import mqtt_connector
from HTCSPythonUtil import config
from car import Car, DetailedCarTracker, Lane, AccelerationState, Command


logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)

lock = threading.Lock()
INTERVAL_MS = 100


def give_command(car: Car, command: Command):
    if command == car.last_command and car.lane == car.lane_when_last_command:
        return
    # If the C-code changes its state internally, this will catch it
    # Maybe not good logic if car gets several commands in one iteration
    if unnecessary_comand(car,command):
        return
    topic = config["base_topic"] + "/" + str(car.id) + "/command"
    logger.debug(f"{command.name} sent to car with id {car.id}")
    mqtt_connector.client_1.publish(topic, command.value, config["quality_of_service"])
    car.last_command = command
    car.lane_when_last_command = car.lane


def unnecessary_comand(car: Car, command: Command):
    return ((car.acceleration_state == AccelerationState.MAINTAINING_SPEED and command == Command.MAINTAIN_SPEED) or 
            (car.acceleration_state == AccelerationState.BRAKING and command == Command.BRAKE) or
            (car.acceleration_state == AccelerationState.ACCELERATING and command == Command.ACCELERATE))


def control_traffic():
    #logger.error("iteration start")
    # for car in local_cars.get_all():
    #     logger.warning(f"car id = {car.id} distance = {car.distance_taken}, lane = {car.lane}")
    for car in local_cars.get_all():
        # in the traffic lane we slow down if we are over our preferred speed. in this case, we also do nothing else
        if car.speed > car.specs.preferred_speed * 1.05 and car.effective_lane() == Lane.TRAFFIC_LANE:
            give_command(car, Command.BRAKE)
            continue

        # try to get back to traffic lane
        if car.lane == Lane.EXPRESS_LANE and local_cars.can_return_to_traffic_lane(car):
            give_command(car, Command.CHANGE_LANE)
        # try to get into traffic lane
        elif car.lane == Lane.MERGE_LANE and local_cars.can_merge_in(car):
            give_command(car, Command.CHANGE_LANE)

        # if we are too close to the one ahead us
        car_directly_ahead = local_cars.car_directly_ahead_in_effective_lane(car, car.effective_lane())
        if car_directly_ahead is not None \
                and car_directly_ahead.distance_taken - car.distance_taken < 1 * car.follow_distance(safety_factor = 1.2):
#                and car.speed > car_directly_ahead.speed:
            decide_brake_or_overtake(car)
        # if we aren't too close we accelerate if we are far enough, otherwise try to overtake
        # this is needed, so cars do not get stuck behind each other, and also, who has already switched lanes,
        # into express, should accelerate
        elif car.speed < car.specs.preferred_speed:
            if car.acceleration_state != AccelerationState.ACCELERATING \
                    and (car_directly_ahead is None
                         or car_directly_ahead.distance_taken - car.distance_taken > car.follow_distance(safety_factor = 2)
                         or car_directly_ahead.speed > car.specs.preferred_speed):
                give_command(car, Command.ACCELERATE)
        elif car.lane == Lane.EXPRESS_LANE and car.speed < car.specs.max_speed:
            give_command(car, Command.ACCELERATE)


def decide_brake_or_overtake(car: Car):
    # in the express lane we brake by all means
    if car.effective_lane() == Lane.EXPRESS_LANE:
        give_command(car, Command.BRAKE)
    # in the merge lane we merge in if possible, otherwise brake
    elif car.effective_lane() == Lane.MERGE_LANE:
        if local_cars.can_merge_in(car):
            give_command(car, Command.CHANGE_LANE)
        else:
            give_command(car, Command.BRAKE)
    # in the traffic lane we overtake. This function checks, that we have to be IN the traffic lane (not in 1 or 4)
    else:
        # case of effective Traffic lane
        # check if it make sense to overtakte the car ahead of us
        car_directly_ahead = local_cars.car_directly_ahead_in_effective_lane(car, car.effective_lane())
        if (car.speed > car_directly_ahead.speed and
            car.specs.preferred_speed > car_directly_ahead.specs.preferred_speed and
            local_cars.can_overtake(car)):
            give_command(car, Command.CHANGE_LANE)
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
