import time
import logging
import itertools
import mqtt_connector
from car import Car
from typing import List
from HTCSPythonUtil import local_cars, config

logger = logging.getLogger(__name__)


def check_collision(_c1: Car, _c2: Car):
    if _c1.lane == _c2.lane:
        diff = abs(_c1.distance_taken - _c2.distance_taken)
        return diff < _c1.specs.size / 2 + _c2.specs.size / 2
    else:
        return False


def send_terminate(_car: Car):
    topic = config["base_topic"] + "/" + str(_car.id) + "/command"
    message = 4
    qos = config["quality_of_service"]
    mqtt_connector.client_1.publish(topic, message, qos)
    logger.debug(f"Terminate command sent to {_car.id}")


def send_notification(_car_id_1: str, _car_id_2: str):
    topic = config["base_topic"] + "/terminator"
    message = _car_id_1 + "," + _car_id_2
    qos = config["quality_of_service"]
    mqtt_connector.client_1.publish(topic, message, qos)
    logger.debug("Notification sent")


if __name__ == "__main__":
    mqtt_connector.setup_connector()

    while True:
        time.sleep(1)

        cars: List[Car] = list(local_cars.values())
        for c1, c2 in itertools.combinations(cars, 2):
            if check_collision(c1, c2):
                logger.info(f"Collision detected: {c1.id} - {c2.id}")
                send_notification(c1.id, c2.id)
                send_terminate(c1)
                send_terminate(c2)

