import os
import ast
import logging
import paho.mqtt.client as mqtt


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("MQTT_Connector")
# TODO: set C level maximum for position
# TODO: maybe create shared constants (enums) between c and python
local_cars = {}
mqtt_connector = mqtt.Client()


def get_connection_config():
    config_dict = dict("".join(l.split()).split("=") for l
                       in open(os.path.dirname(os.path.abspath(__file__)) + "/connection.properties")
                       if not l.strip().startswith("#") )
    config_dict["position_bound"] = int(config_dict["position_bound"])
    config_dict["max_car_size"] = int(config_dict["max_car_size"])
    config_dict["quality_of_service"] = int(config_dict["quality_of_service"])
    return config_dict


def on_message(mqttc, obj, msg):
    topic_parts = msg.topic.split('/')
    if topic_parts[1] == "vehicles":
        car_id = topic_parts[-2]
        msg_type = topic_parts[-1]
        if msg_type == "join":
            if car_id in local_cars.keys():
                logger.warning(f"Car with already existing id ({car_id}) sent a join message")
            else:
                try:
                    specs = ast.literal_eval("{" + msg.payload.decode("utf-8") + "}")
                    local_cars[car_id] = Car(car_id,0, 0, 0, 0, CarSpecs(**specs))
                except TypeError:
                    logger.warning(f"Received a badly formatted join message from id {car_id}: {msg.payload.decode('utf-8')}")
        elif msg_type == "state":
            if car_id not in local_cars.keys():
                logger.warning(f"Car with unrecognized id ({car_id}) sent a state message")
            else:
                try:
                    state = ast.literal_eval("{" + msg.payload.decode("utf-8") + "}")
                    local_cars[car_id].update_state(**state)
                except TypeError:
                    logger.warning(f"Received a badly formatted state message from id {car_id}: {msg.payload.decode('utf-8')}")
        elif msg_type == "command":
            pass                # I think only visualizer should print in this case, but add an info message if needed
        else:
            logger.warning(f"Unrecognized topic: {msg_type}")


def on_connect(mqttc, obj, flags, rc):
    if rc == 0:
        mqtt_connector.connected_flag = True
        print("Connected OK. Returned code =", rc)
    else:
        print("Bad connection. Returned code = ", rc)
        exit(rc)


def setup_connector(config,on_connect=on_connect,on_message=on_message):
    mqtt_connector.username_pw_set(username=config["username"], password=config["password"])
    mqtt_connector.on_connect = on_connect
    mqtt_connector.on_message = on_message
    mqtt_connector.connect(config["address"], 1883, 60)
    mqtt_connector.subscribe(config["base_topic"], config["quality_of_service"])


class CarSpecs:
    def __init__(self, preferred_speed, max_speed, acceleration, braking_power, size):
        self.preferred_speed = preferred_speed
        self.max_speed = max_speed
        self.braking_power = braking_power
        self.acceleration = acceleration
        self.size = size


class Car:
    def __init__(self, car_id, distance_taken, lane, speed, acceleration_state, specs: CarSpecs):
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

    @classmethod
    def for_visualization(cls, distance_taken, lane, size):
        """
        Second constructor, since the visualization doesn't need the whole class
        """
        return cls(None, distance_taken, lane, None, None, CarSpecs(None, None, None, None, size))

    def update_state(self, lane, distance_taken, speed, acceleration_state):
        self.lane = lane
        self.distance_taken = distance_taken
        self.speed = speed
        self.acceleration_state = acceleration_state

    def get_relative_position(self, config):
        return self.distance_taken / config["position_bound"]
