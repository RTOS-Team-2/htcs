import os
import ast
import paho.mqtt.client as mqtt


# TODO: set C level maximum for position
# TODO: maybe create shared constants (enums) between c and python
local_cars = {}
mqtt_connector = mqtt.Client()


def getConnectionConfig():
    config_dict = dict("".join(l.split()).split("=") for l
                       in open(os.path.dirname(os.path.abspath(__file__)) + "/connection.properties")
                       if not l.strip().startswith("#") )
    config_dict["position_bound"] = int(config_dict["position_bound"])
    config_dict["max_car_size"] = int(config_dict["max_car_size"])
    config_dict["quality_of_service"] = int(config_dict["quality_of_service"])
    return config_dict


def onMessage(mqttc, obj, msg):
    topicParts = msg.topic.split('/')
    if topicParts[1] == "vehicles":
        carId = topicParts[-2]
        msgType = topicParts[-1]
        if msgType == "join":
            if carId in local_cars.keys():
                raise KeyError("Car with already existing id sent a join message")
            specs = ast.literal_eval("{" + msg.payload.decode("utf-8") + "}")
            local_cars[carId] = Car(0, 0, 0, 0, CarSpecs(**specs))
        elif msgType == "state":
            if carId not in local_cars.keys():
                raise KeyError("Car with unrecognized id sent a state message")
            state = ast.literal_eval("{" + msg.payload.decode("utf-8") + "}")
            local_cars[carId].updateState(**state)

        else:
            raise NotImplementedError("unrecognized topic")


def onConnect(mqttc, obj, flags, rc):
    if rc == 0:
        mqtt_connector.connected_flag = True        #set flag
        print("Connected OK. Returned code =", rc)
    else:
        print("Bad connection. Returned code = ", rc)
        exit(rc)


def setUpConnector():
    mqtt_connector.username_pw_set(username=CONNECTION_CONFIG["username"], password=CONNECTION_CONFIG["password"])
    mqtt_connector.on_connect = onConnect
    mqtt_connector.on_message = onMessage
    mqtt_connector.connect(CONNECTION_CONFIG["address"], 1883, 60)
    mqtt_connector.subscribe(CONNECTION_CONFIG["base_topic"], CONNECTION_CONFIG["quality_of_service"])


class CarSpecs:
    def __init__(self, preferredSpeed, maxSpeed, acceleration, brakingPower, size):
        self.preferredSpeed = preferredSpeed
        self.maxSpeed = maxSpeed
        self.brakingPower = brakingPower
        self.acceleration = acceleration
        self.size = size


class Car:
    def __init__(self, distanceTaken, lane, speed, accelerationState, specs: CarSpecs):
        """
        :param distanceTaken: distance taken along the single axis
        :param lane: ENUM TODO: what means what + typehint
        :param speed:
        :param accelerationState: enum TODO: what means what + typehint
        :param specs: constant parameters of the car
        """
        self.distanceTaken = distanceTaken
        self.lane = lane
        self.speed = speed
        self.accelerationState = accelerationState
        self.specs = specs

    @classmethod
    def forVisualization(cls, distanceTaken, lane, size):
        """
        Second constructor, since the visualization doesn't need the whole class
        """
        return cls(distanceTaken, lane, None, None, CarSpecs(None, None, None, None, size))

    def updateState(self, lane, distanceTaken, speed, accelerationState):
        self.lane = lane
        self.distanceTaken = distanceTaken
        self.speed = speed
        self.accelerationState = accelerationState

    def getRelativePosition(self):
        return self.distanceTaken / CONNECTION_CONFIG["position_bound"]
