import os
import ast
import uuid
import logging
import paho.mqtt.client as mqtt
from concurrent.futures import ThreadPoolExecutor
from typing import Dict


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("MQTT_Connector")
# TODO: set C level maximum for position
# TODO: maybe create shared constants (enums) between c and python
local_cars = {}
mqtt_client_1 = mqtt.Client("main_client_" + str(uuid.uuid4()))
mqtt_client_2 = mqtt.Client("state_client_" + str(uuid.uuid4()))
thread_pool_executor = ThreadPoolExecutor(20)


def get_connection_config():
    config_dict = dict("".join(l.split()).split("=") for l
                       in open(os.path.dirname(os.path.abspath(__file__)) + "/connection.properties")
                       if not l.strip().startswith("#") )
    config_dict["position_bound"] = int(config_dict["position_bound"])
    config_dict["quality_of_service"] = int(config_dict["quality_of_service"])
    return config_dict


CONFIG: Dict[str, any] = get_connection_config()


def on_join_message(client, user_data, msg):
    car_id = msg.topic.split('/')[-2]
    car = local_cars.get(car_id)
    if car is None:
        specs = ast.literal_eval("{" + msg.payload.decode("utf-8") + "}")
        create_car_fun = user_data
        local_cars[car_id] = create_car_fun(car_id, CarSpecs(**specs))
    else:
        logger.warning(f"Car with already existing id ({car_id}) sent a join message")


def process_message(msg):
    car_id = msg.topic.split('/')[-2]
    car = local_cars.get(car_id)
    if car is None:
        logger.warning(f"Car with unrecognized id ({car_id}) sent a state message")
    else:
        state = ast.literal_eval("{" + msg.payload.decode("utf-8") + "}")
        local_cars[car_id].update_state(**state)


def on_state_message(client, user_data, msg):
    thread_pool_executor.submit(process_message, msg)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True
    else:
        print("Bad connection. Returned code = ", rc)
        exit(rc)


def on_disconnect(client, userdata, rc):
    print(client.client_id, " disconnected, return code = ", rc)


def create_car(car_id, specs):
    return Car(car_id, specs)


def setup_connectors(create_car_fun=create_car):
    mqtt_client_1.user_data_set(create_car_fun)
    mqtt_client_1.username_pw_set(username=CONFIG["username"], password=CONFIG["password"])
    mqtt_client_1.on_connect = on_connect
    mqtt_client_1.on_message = on_join_message
    mqtt_client_1.on_disconnect = on_disconnect

    mqtt_client_2.username_pw_set(username=CONFIG["username"], password=CONFIG["password"])
    mqtt_client_2.on_connect = on_connect
    mqtt_client_2.on_message = on_state_message
    mqtt_client_2.on_disconnect = on_disconnect

    mqtt_client_1.connect(CONFIG["address"])
    mqtt_client_1.loop_start()
    mqtt_client_1.subscribe(topic=CONFIG["base_topic"] + "/+/join", qos=CONFIG["quality_of_service"])

    mqtt_client_2.connect(CONFIG["address"])
    mqtt_client_2.loop_start()
    mqtt_client_2.subscribe(CONFIG["base_topic"] + "/+/state", CONFIG["quality_of_service"])


def cleanup_connectors():
    mqtt_client_1.loop_stop()
    mqtt_client_2.loop_stop()


class CarSpecs:
    def __init__(self, preferred_speed=0, max_speed=0, acceleration=0, braking_power=0, size=0):
        self.preferred_speed = preferred_speed
        self.max_speed = max_speed
        self.braking_power = braking_power
        self.acceleration = acceleration
        self.size = size


class Car:
    def __init__(self, car_id, specs: CarSpecs, distance_taken=0, lane=0, speed=0, acceleration_state=0):
        """
        :param distance_taken: distance taken along the single axis
        :param lane: ENUM TODO: what means what + typehint
        :param speed:
        :param acceleration_state: enum TODO: what means what + typehint
        :param specs: constant parameters of the car
        """
        
        self.id = car_id
        self.distance_taken = distance_taken
        self.lane = lane
        self.speed = speed
        self.acceleration_state = acceleration_state
        self.specs = specs

    def update_state(self, lane, distance_taken, speed, acceleration_state):
        self.lane = lane
        self.distance_taken = distance_taken
        self.speed = speed
        self.acceleration_state = acceleration_state

    def get_relative_position(self, config):
        return self.distance_taken / config["position_bound"]
