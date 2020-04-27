import cv2
import numpy as np
from typing import List


class Car:
    def __init__(self, pos, lane):
        self.pos = pos
        self.lane = lane


def display_state(map_image: np.ndarray, car_image: np.ndarray, cars: List[Car]):
    vis = map_image.copy()
    y_start = int(map_image.shape[0] - cars[0].pos - car_image.shape[0] / 2)
    part = vis[y_start: y_start + car_image.shape[0], 40 : 40 + car_image.shape[1], :]
    part = np.minimum(car_image, part)
    vis[y_start: y_start + car_image.shape[0], 40 : 40 + car_image.shape[1], :] = part
    cv2.imshow("visu", vis)
    cv2.waitKey(10)


cv2.namedWindow("visu", flags=cv2.WINDOW_NORMAL)
cars = [Car(100, 0)]
map = cv2.imread("map.png")
car = cv2.resize(cv2.imread("car.png"), (48, 48))
a = car == 0
counter = 0
while counter < 600:
    cars[0].pos += 1
    display_state(map, car, cars)



