import os
import cv2
import random
import logging
from tkinter import Tk
from car import Car, CarSpecs
from HTCSPythonUtil import config

if os.name == "nt":
    # https://github.com/opencv/opencv/issues/11360
    import ctypes
    # Set DPI Awareness  (Windows 10 and 8)
    _ = ctypes.windll.shcore.SetProcessDpiAwareness(2)
    # the argument is the awareness level, which can be 0, 1 or 2:
    # for 1-to-1 pixel control I seem to need it to be non-zero (I'm using level 2)


logger = logging.getLogger(__name__)
tk = Tk()
window_width = tk.winfo_screenwidth()
black_region_height = 100
# image resources
WINDOW_NAME = "Highway Traffic Control System Visualization"
im_bigmap = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/map.png")
im_minimap = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/minimap.png")
red_car_straight = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/car1.png")
red_car_left = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/car1left.png")
red_car_right = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/car1right.png")
blue_car_straight = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/car2.png")
blue_car_left = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/car2left.png")
blue_car_right = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/car2right.png")
truck = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/truck.png")
explosion = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/explosion.png")
title = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/title.png")
try:
    _ = [im_bigmap.shape[0], im_minimap.shape[0], red_car_straight.shape[0], red_car_left.shape[0],
         red_car_right.shape[0], blue_car_straight.shape[0], blue_car_left.shape[0], blue_car_right.shape[0],
         truck.shape[0], explosion.shape[0], title.shape[0]]
except AttributeError:
    logger.critical("Some image resources were not found.")
# to fit screen
im_minimap = cv2.resize(im_minimap, (window_width, im_minimap.shape[0]))
title = cv2.resize(title, (window_width, black_region_height))
logger.info(f"Window width will be set to {window_width} pixels.")
# measure
minimap_length_pixel = im_minimap.shape[1]
minimap_height_pixel = im_minimap.shape[0]
bigmap_length_pixel = im_bigmap.shape[1]
# fix parameters
region_width_meter_start = 200
map_height_meter = 16
map_length_meter = config["position_bound"]
center_fast_lane_mini = 32
center_slow_lane_mini = 80
center_merge_lane_mini = 130
detail_height = int(window_width * map_height_meter / region_width_meter_start)
y_stretch = detail_height / im_bigmap.shape[0]
center_fast_lane = 42.5 * y_stretch
center_slow_lane = 103.5 * y_stretch
center_merge_lane = 164 * y_stretch
car_height = int((center_slow_lane - center_fast_lane) * 0.8)
x_scale_minimap = minimap_length_pixel / map_length_meter
x_scale_bigmap = bigmap_length_pixel / map_length_meter


class CarImage(Car):
    def __init__(self, car_id, specs: CarSpecs, state):
        # Create Car
        super().__init__(car_id, specs, state)
        if specs.size > 7.5:
            self.straight = truck
            self.left = truck
            self.right = truck
            self.color = (11, 195, 255)
            self.text_color = self.color
        # Red or Blue
        elif bool(random.getrandbits(1)):
            self.straight = red_car_straight
            self.left = red_car_left
            self.right = red_car_right
            self.color = (0, 0, 255) # BGR
            self.text_color = self.color
        else:
            self.straight = blue_car_straight
            self.left = blue_car_left
            self.right = blue_car_right
            self.color = (255, 0, 0) # BGR
            self.text_color = (253, 177, 0) # BGR
        # At least we set the height, but width will be dependent on the region's width in meter
        self.straight = cv2.resize(self.straight, (self.straight.shape[0], car_height))
        self.left = cv2.resize(self.left, (self.left.shape[0], car_height))
        self.right = cv2.resize(self.right, (self.right.shape[0], car_height))
        self.exploded = False

    def __str__(self):
        return super().__str__()

    def __repr__(self):
        return super().__repr__()

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
        cx = int(self.distance_taken * x_scale_minimap)
        return cx, cy

    def is_in_region(self, region_offset, region_width):
        return self.distance_taken > region_offset and \
               self.distance_taken - self.specs.size < region_offset + region_width

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

    def width_pixel(self, region_width_meter):
        return int(self.specs.size / region_width_meter * window_width)

    def get_x_slice_and_image(self, offset_region, width_region):
        w_px_car = self.width_pixel(width_region)
        on_vis_slice_x_end = int((self.distance_taken - offset_region) / width_region * window_width)
        on_vis_slice_x_start = on_vis_slice_x_end - w_px_car
        on_car_slice_x_start = 0
        on_car_slice_x_end = w_px_car
        if on_vis_slice_x_end > window_width:
            on_car_slice_x_end -= on_vis_slice_x_end - window_width
            on_vis_slice_x_end = window_width
        elif on_vis_slice_x_start < 0:
            on_car_slice_x_start -= on_vis_slice_x_start
            on_vis_slice_x_start = 0
        car_x_slice = slice(on_car_slice_x_start, on_car_slice_x_end)
        return slice(on_vis_slice_x_start, on_vis_slice_x_end), self.get_image(w_px_car, car_x_slice)

    def get_image(self, car_width_pixel, x_slice):
        if self.distance_taken > map_length_meter - 30 or self.exploded:
            im = explosion
        elif self.lane in [1, 3]:
            im = self.left
        elif self.lane == 4:
            im = self.right
        else:
            im = self.straight
        return cv2.resize(im, (car_width_pixel, car_height))[:, x_slice, :]
