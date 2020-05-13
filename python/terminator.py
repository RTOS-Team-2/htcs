import time
import logging
import itertools
import mqtt_connector
from car import Car, CarManager
from typing import List
from HTCSPythonUtil import config

logger = logging.getLogger(__name__)

INTERVAL_MS = 500


def check_collision(_c1: Car, _c2: Car):
    if _c1.lane == _c2.lane:
        diff = _c1.distance_taken - _c2.distance_taken
        return diff < _c1.specs.size if diff > 0 else abs(diff) < _c2.specs.size
    else:
        return False


def send_terminate(_car_id: str):
    topic = config["base_topic"] + "/" + _car_id + "/command"
    message = 4
    qos = config["quality_of_service"]
    mqtt_connector.client_1.publish(topic, message, qos)
    logger.debug(f"Terminate command sent to {_car_id}")


def publish_obituary(_car_id: str):
    topic = config["base_topic"] + "/obituary"
    qos = config["quality_of_service"]
    mqtt_connector.client_1.publish(topic, _car_id, qos)
    logger.debug(f"Obituary published about {_car_id}")


if __name__ == "__main__":
    local_cars = CarManager()
    mqtt_connector.setup_connector(local_cars)

    # TODO find a better solution, maybe received state flag ?
    # sleeping for 3 seconds to receive all the join messages and their first state messages
    logger.info("The terminator is getting ready... 'I'll be back'")
    time.sleep(3)
    logger.info("'I'm back'")
    interval_sec = INTERVAL_MS / 1000
    while True:
        time.sleep(interval_sec)

        cars: List[Car] = list(local_cars.values())
        cars_to_be_terminated = set([c.id for c in cars if c.distance_taken >= config["position_bound"]])
        if len(cars_to_be_terminated) > 0:
            logger.info(f"Cars reached the end of the road and will be terminated: {cars_to_be_terminated}")
        for c1, c2 in itertools.combinations(cars, 2):
            if check_collision(c1, c2):
                logger.info(f"Collision detected: {c1.id} - {c2.id}")
                cars_to_be_terminated.add(c1.id)
                cars_to_be_terminated.add(c2.id)

        for car_id in cars_to_be_terminated:
            publish_obituary(car_id)
            send_terminate(car_id)
