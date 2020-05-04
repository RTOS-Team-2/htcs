import ast
import paho.mqtt.client as mqtt


# TODO: set C level maximum for position
# TODO: maybe create shared constants (enums) between c and python
POSITION_BOUND = 10000
MAX_CAR_SIZE = 6
CARSTARTINGSPEED = 13.888889


localCars = {}
MQTTCONNECTOR = mqtt.Client()
PASSWORD = "password"
USERNAME = "krisz.kern@gmail.com"
ADDRESS = "maqiatto.com"
BASETOPIC = "krisz.kern@gmail.com/vehicles/#"
QUALITYOFSERVICE = 1


def onMessage(mqttc, obj, msg):
    topicParts = msg.topic.split('/')
    if topicParts[1] == "vehicles":
        carId = topicParts[-2]
        msgType = topicParts[-1]
        if msgType == "join":
            if carId in localCars.keys():
                raise KeyError("Car with already existing id sent a join message")
            specs = ast.literal_eval("{" + msg.payload.decode("utf-8") + "}")
            localCars[carId] = Car(0, 0, CARSTARTINGSPEED, 0, CarSpecs(**specs))
        elif msgType == "state":
            if carId not in localCars.keys():
                raise KeyError("Car with unrecognized id sent a state message")
            state = ast.literal_eval("{" + msg.payload.decode("utf-8") + "}")
            localCars[carId].updateState(**state)

        else:
            raise NotImplementedError("unrecognized topic")


def onConnect(mqttc, obj, flags, rc):
    if rc == 0:
        MQTTCONNECTOR.connected_flag = True  #set flag
        print("Connected OK. Returned code =", rc)
    else:
        print("Bad connection. Returned code = ", rc)
        exit(rc)


def setUpConnector():
    MQTTCONNECTOR.username_pw_set(username=USERNAME, password=PASSWORD)
    MQTTCONNECTOR.on_connect = onConnect
    MQTTCONNECTOR.on_message = onMessage
    MQTTCONNECTOR.connect(ADDRESS, 1883, 60)
    MQTTCONNECTOR.subscribe(BASETOPIC, QUALITYOFSERVICE)


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
        return self.distanceTaken / POSITION_BOUND
