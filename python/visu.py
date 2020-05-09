import os
import cv2
import random
import logging
import threading
import numpy as np
import mqtt_connector
from car import Car, CarSpecs
from HTCSPythonUtil import config, local_cars


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# SOME GLOBAL VARIABLES
commands = dict([(0, "Maintain speed!"), (1, "Accelerate!"), (2, "Brake!"), (3, "Switch lanes!"), (4, "Terminate!")])
# image resources
WINDOW_NAME_MINIMAP = "Highway Traffic Control System Minimap"
WINDOW_NAME_VISU = "Highway Traffic Control System Visualization"
im_bigmap = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/mapp_big.png")
im_minimap = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/mapp.png")
red_car_straight = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/car1.png")
red_car_left = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/car1left.png")
red_car_right = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/car1right.png")
blue_car_straight = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/car2.png")
blue_car_left = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/car2left.png")
blue_car_right = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/car2right.png")
# view managing
# will never change
minimap_length_pixel = im_minimap.shape[1]
minimap_height_pixel = im_minimap.shape[0]
bigmap_length_pixel = im_bigmap.shape[1]
map_length_meter = config["position_bound"]
map_width_meter = 20
x_scale_minimap = minimap_length_pixel / map_length_meter
x_scale_bigmap = bigmap_length_pixel / map_length_meter
region_width_meter = 350
visu_window_width = 1800
visu_window_height = int(visu_window_width * map_width_meter / region_width_meter)
y_stretch = visu_window_height / im_bigmap.shape[0]
center_fast_lane = 42.5 * y_stretch
center_slow_lane = 103.5 * y_stretch
center_merge_lane = 164 * y_stretch
center_fast_lane_mini = 32
center_slow_lane_mini = 80
center_merge_lane_mini = 130
car_height = int((center_slow_lane - center_fast_lane) * 0.7)
# will change
is_dragging = False
offset_meter = 0
offset_minimap_pixel = int(offset_meter * x_scale_minimap)
region_width_minimap_pixel = int(region_width_meter * x_scale_minimap)
offset_bigmap_pixel = int(offset_meter * x_scale_bigmap)
region_width_bigmap_pixel = int(region_width_meter * x_scale_bigmap)
drag_start_x = 0
drag_start_offset = 0


# class for visualization
class CarImage(Car):
    def __init__(self, car_id, specs: CarSpecs):
        # Create Car
        super().__init__(car_id, specs)
        # Red or Blue
        if bool(random.getrandbits(1)):
            self.straight = red_car_straight
            self.left = red_car_left
            self.right = red_car_right
            self.color = (0, 0, 255) # BGR
        else:
            self.straight = blue_car_straight
            self.left = blue_car_left
            self.right = blue_car_right
            self.color = (255, 0, 0) # BGR
        # Scale to correct size
        new_w = int(self.specs.size * x_scale_bigmap * visu_window_width / region_width_bigmap_pixel)
        self.straight = cv2.resize(self.straight, (new_w, car_height))
        self.left = cv2.resize(self.left, (new_w, car_height))
        self.right = cv2.resize(self.right, (new_w, car_height))

    def get_y_slice(self):
        start = 0
        if self.lane == 0:
            start = int(center_merge_lane - self.straight.shape[0] / 2)
        elif self.lane == 1:
            start = int((center_merge_lane + center_slow_lane) / 2 - self.straight.shape[0] / 2)
        elif self.lane == 2:
            start = int(center_slow_lane - self.straight.shape[0] / 2)
        elif self.lane in [3, 4]:
            start = int((center_slow_lane + center_fast_lane) / 2 - self.straight.shape[0] / 2)
        elif self.lane == 5:
            start = int(center_fast_lane - self.straight.shape[0] / 2)
        return slice(start, start + self.straight.shape[0])

    def get_x_slice(self):
        on_vis_slice_x_end = int((self.distance_taken - offset_meter) / region_width_meter * visu_window_width)
        on_vis_slice_x_start = on_vis_slice_x_end - self.straight.shape[1]
        on_car_slice_x_start = 0
        on_car_slice_x_end = self.straight.shape[1]
        if on_vis_slice_x_end > visu_window_width:
            on_car_slice_x_end -= on_vis_slice_x_end - visu_window_width
            on_vis_slice_x_end = visu_window_width
        elif on_vis_slice_x_start < 0:
            on_car_slice_x_start -= on_vis_slice_x_start
            on_vis_slice_x_start = 0
        return slice(on_vis_slice_x_start, on_vis_slice_x_end), slice(on_car_slice_x_start, on_car_slice_x_end)

    def is_in_region(self):
        return self.distance_taken > offset_meter and \
               self.distance_taken - self.specs.size < offset_meter + region_width_meter

    def get_point_on_minimap(self):
        cy = 0
        if self.lane == 0:
            cy = center_merge_lane_mini
        elif self.lane == 1:
            cy = int((center_merge_lane_mini + center_slow_lane_mini) / 2)
        elif self.lane == 2:
            cy = center_slow_lane_mini
        elif self.lane in [3, 4]:
            cy = int((center_slow_lane_mini + center_fast_lane_mini) / 2)
        elif self.lane == 5:
            cy = center_fast_lane_mini
        cx = int(self.distance_taken / map_length_meter * minimap_length_pixel)
        return cx, cy

    def get_image(self):
        if self.lane in [0, 2, 5]:
            return self.straight
        elif self.lane in [1, 3]:
            return self.left
        elif self.lane == 4:
            return self.right


def minimap_move(event, x, y, flags, param):
    global offset_minimap_pixel, drag_start_x, drag_start_offset, is_dragging, offset_meter
    if event == cv2.EVENT_LBUTTONDOWN and offset_minimap_pixel <= x <= offset_minimap_pixel + region_width_minimap_pixel:
        drag_start_x = x
        drag_start_offset = offset_minimap_pixel
        is_dragging = True
    elif event == cv2.EVENT_MOUSEMOVE and is_dragging:
        offset_minimap_pixel = max(0, min(drag_start_offset + x - drag_start_x, minimap_length_pixel - region_width_minimap_pixel))
        offset_meter = offset_minimap_pixel / x_scale_minimap
    elif event == cv2.EVENT_LBUTTONUP:
        is_dragging = False


if __name__ == "__main__":
    mqtt_connector.setup_connector(CarImage)
    lock = threading.Lock()

    cv2.namedWindow(WINDOW_NAME_MINIMAP, cv2.WINDOW_FREERATIO)
    cv2.resizeWindow(WINDOW_NAME_MINIMAP, 1700, 150)
    cv2.setMouseCallback(WINDOW_NAME_MINIMAP, minimap_move)

    cv2.namedWindow(WINDOW_NAME_VISU, cv2.WINDOW_FREERATIO)
    cv2.resizeWindow(WINDOW_NAME_VISU, visu_window_width, visu_window_height)

    while cv2.getWindowProperty(WINDOW_NAME_MINIMAP, 0) >= 0 and cv2.getWindowProperty(WINDOW_NAME_VISU, 0) >= 0:
        cur_im_minimap = im_minimap.copy()
        # gray out
        cur_im_minimap[:, : offset_minimap_pixel, :] = \
            (cur_im_minimap[:, : offset_minimap_pixel, :] * 0.6).astype(np.int32)
        cur_im_minimap[:, offset_minimap_pixel + region_width_minimap_pixel:, :] = \
            (cur_im_minimap[:, offset_minimap_pixel + region_width_minimap_pixel:, :] * 0.6).astype(np.int32)
        # orange lines
        cv2.line(cur_im_minimap,
                 (offset_minimap_pixel, 0),
                 (offset_minimap_pixel, minimap_height_pixel),
                 (0, 140, 255),
                 3)
        cv2.line(cur_im_minimap,
                 (offset_minimap_pixel + region_width_minimap_pixel, 0),
                 (offset_minimap_pixel + region_width_minimap_pixel, minimap_height_pixel),
                 (0, 140, 255),
                 3)

        # visualizer scaling.... :/
        offset_bigmap_pixel = int(offset_meter * x_scale_bigmap)
        vis = cv2.resize(im_bigmap[:, offset_bigmap_pixel: offset_bigmap_pixel + region_width_bigmap_pixel, :],
                         (visu_window_width, visu_window_height),
                         interpolation=cv2.INTER_NEAREST)
        with lock:
            cars = list(local_cars.values())
        for car in cars:
            x, y = car.get_point_on_minimap()
            cv2.circle(cur_im_minimap, (x, y), 3, car.color, cv2.FILLED)
            if car.is_in_region():
                x_slice_vis, x_slice_car = car.get_x_slice()
                vis[car.get_y_slice(), x_slice_vis, :] = car.get_image()[:, x_slice_car, :]

        # scale up
        cur_im_minimap[:, offset_minimap_pixel: offset_minimap_pixel + region_width_minimap_pixel, :] = \
            cv2.resize(cur_im_minimap[int(minimap_height_pixel * 0.05): int(minimap_height_pixel * 0.90),
                                      offset_minimap_pixel: offset_minimap_pixel + region_width_minimap_pixel,
                                      :],
                       (region_width_minimap_pixel, minimap_height_pixel))

        cv2.imshow(WINDOW_NAME_MINIMAP, cur_im_minimap)
        cv2.imshow(WINDOW_NAME_VISU, vis)
        cv2.waitKey(1)

    cv2.destroyAllWindows()
    mqtt_connector.cleanup_connector()

