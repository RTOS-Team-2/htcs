import os
import cv2
import ast
import random
import numpy as np
from HTCSPythonUtil import mqtt_connector, getConnectionConfig, local_cars, Car, onConnect


# SOME GLOBAL VARIABLES
CONNECTION_CONFIG = getConnectionConfig()
# image resources
WINDOW_NAME = "Highway Traffic Control System Visualization"
imMap = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/map.png")
redCarStraight = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/car1.png")
redCarLeft = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/car1left.png")
redCarRight = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/car1right.png")
blueCarStraight = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/car2.png")
blueCarleft = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/car2left.png")
blueCarRight = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/car2right.png")
# for calculations
mapLength = imMap.shape[1]
centerFastLane = 176
centerSlowLane = 298
centerMergeLane = 420
maxCarSizePixel = centerSlowLane - centerFastLane
# for navigation
currentOffset = 0
currentRegionWidth = mapLength


# TODO: error raising does not do anything on that thread
def onMessageVis(mqttc, obj, msg):
    topicParts = msg.topic.split('/')
    if topicParts[1] == "vehicles":
        carId = topicParts[-2]
        msgType = topicParts[-1]
        print(msgType)
        if msgType == "join":
            if carId in local_cars.keys():
                raise KeyError("Car with already existing id sent a join message")

            specs = ast.literal_eval("{" + msg.payload.decode("utf-8") + "}")
            local_cars[carId] = CarImage(0, 0, specs['size'])

        elif msgType == "state":
            if carId not in local_cars.keys():
                raise KeyError("Car with unrecognized id sent a state message")

            state = ast.literal_eval("{" + msg.payload.decode("utf-8") + "}")
            local_cars[carId].car.updateState(**state)

        else:
            raise NotImplementedError("unrecognized topic")


# class for visualization
class CarImage:
    def __init__(self, distanceTaken, lane, size):
        # Create Car
        self.car = Car.forVisualization(distanceTaken, lane, size)
        # Red or Blue
        if bool(random.getrandbits(1)):
            self.straight = redCarStraight
            self.left = redCarLeft
            self.right = redCarRight
        else:
            self.straight = blueCarStraight
            self.left = blueCarleft
            self.right = blueCarRight
        # Scale to correct size
        origH, origW = self.straight.shape[:2]
        newW = np.round(maxCarSizePixel * self.car.specs.size / CONNECTION_CONFIG["max_car_size"]).astype(np.int32)
        newH = np.round(origH * newW / origW).astype(np.int32)
        self.straight = cv2.resize(self.straight, (newW, newH))
        self.left = cv2.resize(self.left, (newW, newH))
        self.right = cv2.resize(self.right, (newW, newH))

    def getYSlice(self):
        if self.car.lane == 0:
            start = int(centerMergeLane - self.straight.shape[0] / 2)
        elif self.car.lane in [1, 2]:
            start = int((centerMergeLane + centerSlowLane) / 2 - self.straight.shape[0] / 2)
        elif self.car.lane == 3:
            start = int(centerSlowLane - self.straight.shape[0] / 2)
        elif self.car.lane in [4, 5, 6, 7]:
            start = int((centerSlowLane + centerFastLane) / 2 - self.straight.shape[0] / 2)
        else:   # 8
            start = int(centerFastLane - self.straight.shape[0] / 2)
        return slice(start, start + self.straight.shape[0])

    def getXSlice(self):
        possibleMaximum = mapLength - self.straight.shape[1]
        start = np.floor(possibleMaximum * self.car.getRelativePosition()).astype(np.int32)
        return slice(start, start + self.straight.shape[1])

    def getSignaledImage(self):
        if self.car.lane in [0, 3, 8]:
            return self.straight
        elif self.car.lane in [1, 2, 4, 5]:
            return self.left
        elif self.car.lane in [6, 7]:
            return self.right


def display_state(cars):
    global currentOffset, currentRegionWidth

    vis = imMap.copy()
    for carId, car in cars.items():
        vis[car.getYSlice(), car.getXSlice(), :] = car.getSignaledImage()

    c = cv2.waitKey(20)
    if c == ord('a'):
        currentOffset -= 30
    elif c == ord('d'):
        currentOffset += 30
    if c == ord('w'):
        if currentRegionWidth > mapLength * 0.1:
            currentRegionWidth = np.floor(currentRegionWidth * 0.95).astype(np.int32)
            _, _, wW, wH = cv2.getWindowImageRect(WINDOW_NAME)
            cv2.resizeWindow(WINDOW_NAME, wW, int(wH / 0.95))
    elif c == ord('s'):
        newRegionWidth = np.floor(currentRegionWidth / 0.95).astype(np.int32)
        if newRegionWidth <= mapLength:
            currentRegionWidth = newRegionWidth
            _, _, wW, wH = cv2.getWindowImageRect(WINDOW_NAME)
            cv2.resizeWindow(WINDOW_NAME, wW, int(wH * 0.95))
        else:
            currentRegionWidth = mapLength
    currentOffset = max(min(currentOffset, mapLength - currentRegionWidth), 0)

    cv2.imshow(WINDOW_NAME, vis[:, currentOffset: currentOffset + currentRegionWidth, :])


if __name__ == "__main__":
    mqtt_connector.username_pw_set(username=CONNECTION_CONFIG["username"], password=CONNECTION_CONFIG["password"])
    mqtt_connector.on_connect = onConnect
    mqtt_connector.on_message = onMessageVis
    mqtt_connector.connect(CONNECTION_CONFIG["address"], 1883, 60)
    mqtt_connector.subscribe(CONNECTION_CONFIG["base_topic"], CONNECTION_CONFIG["quality_of_service"])
    mqtt_connector.loop_start()

    cv2.namedWindow(WINDOW_NAME, flags=cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 1800, 250)

    while True:
        display_state(local_cars)

