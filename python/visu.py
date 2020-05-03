import cv2
import numpy as np
from typing import List
from python.HTCSPythonUtil import Car


WINDOW_NAME = "Highway Traffic Control System Visualization"
imMap = cv2.imread("python/map.png")
mapLength = imMap.shape[0]
centerFastLane = 69
centerSlowLane = 106
desiredCarSize = int((centerSlowLane - centerFastLane) / 0.6)
xStartFast = centerFastLane - int(desiredCarSize / 2)
xStartSlow = centerSlowLane - int(desiredCarSize / 2)
imCar = cv2.resize(cv2.imread("python/car.png"), (desiredCarSize, desiredCarSize))


def display_state(cars: List[Car]):
    vis = imMap.copy()
    for car in cars:
        y_start = np.floor(mapLength - desiredCarSize - (mapLength - desiredCarSize) * car.getRelativePosition()).astype(np.int32)
        x_start = xStartSlow
        if car.lane == 0:
            x_start = xStartFast
        part = vis[y_start: y_start + desiredCarSize, x_start: x_start + desiredCarSize, :]
        part = np.minimum(imCar, part)
        vis[y_start: y_start + desiredCarSize, x_start: x_start + desiredCarSize, :] = part
    cv2.imshow(WINDOW_NAME, vis)
    cv2.waitKey(20)


if __name__ == "__main__":
    cv2.namedWindow(WINDOW_NAME, flags=cv2.WINDOW_NORMAL)
    cars = []
    cars.append(Car.forVisualization(0, 1))
    cars.append(Car.forVisualization(0, 0))
    d = 0
    while d < 10000:
        cars[0].pos = d
        cars[1].pos = int(d / 2)
        display_state(cars)
        d += 25



