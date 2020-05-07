import os
import cv2
import ast
import random
import logging
import threading
import numpy as np
from typing import List
from HTCSPythonUtil import mqtt_connector, get_connection_config, Car, setup_connector


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# SOME GLOBAL VARIABLES
CONNECTION_CONFIG = get_connection_config()
local_cars = {}
# image resources
WINDOW_NAME_MINIMAP = "Highway Traffic Control System Minimap"
WINDOW_NAME_VISU = "Highway Traffic Control System Visualization"
im_bigmap = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/map_big.png")
im_minimap = cv2.imread(os.path.dirname(os.path.abspath(__file__)) + "/res/minimap.png")
# view managing
# will never change
minimap_length_pixel = im_minimap.shape[1]
minimap_height_pixel = im_minimap.shape[0]
bigmap_length_pixel = im_bigmap.shape[1]
map_length_meter = CONNECTION_CONFIG["position_bound"]
map_width_meter = 19
x_scale_minimap = minimap_length_pixel / map_length_meter
x_scale_bigmap = bigmap_length_pixel / map_length_meter
# will change
go_on = True
is_dragging = False
offset_meter = 0
region_width_meter = 250
offset_minimap_pixel = int(offset_meter * x_scale_minimap)
region_width_minimap_pixel = int(region_width_meter * x_scale_minimap)
drag_start_x = 0
drag_start_offset = 0


def minimap_move(event, x, y, flags, param):
    global offset_minimap_pixel, drag_start_x, drag_start_offset, is_dragging, offset_meter
    if event == cv2.EVENT_LBUTTONDOWN and offset_minimap_pixel <= x <= offset_minimap_pixel + region_width_minimap_pixel:
        drag_start_x = x
        drag_start_offset = offset_minimap_pixel
        is_dragging = True
    elif event == cv2.EVENT_MOUSEMOVE and is_dragging:
        offset_minimap_pixel = max(0, min(drag_start_offset + x - drag_start_x, minimap_length_pixel))
        offset_meter = offset_minimap_pixel / x_scale_minimap
    elif event == cv2.EVENT_LBUTTONUP:
        is_dragging = False


if __name__ == "__main__":
    cv2.namedWindow(WINDOW_NAME_MINIMAP, cv2.WINDOW_FREERATIO)
    cv2.resizeWindow(WINDOW_NAME_MINIMAP, 1700, 150)
    cv2.setMouseCallback(WINDOW_NAME_MINIMAP, minimap_move)

    cv2.namedWindow(WINDOW_NAME_VISU, cv2.WINDOW_FREERATIO)
    region_aspect_ratio = region_width_meter / map_width_meter
    cv2.resizeWindow(WINDOW_NAME_VISU, 1800, int(1800 / region_aspect_ratio))

    while go_on:
        cur_im_minimap = im_minimap.copy()
        # gray out
        cur_im_minimap[:, : offset_minimap_pixel, :] = \
            (cur_im_minimap[:, : offset_minimap_pixel, :] * 0.6).astype(np.int32)
        cur_im_minimap[:, offset_minimap_pixel + region_width_minimap_pixel:, :] = \
            (cur_im_minimap[:, offset_minimap_pixel + region_width_minimap_pixel:, :] * 0.6).astype(np.int32)
        # scale up
        cur_im_minimap[:, offset_minimap_pixel: offset_minimap_pixel + region_width_minimap_pixel, :] = \
            cv2.resize(cur_im_minimap[int(minimap_height_pixel * 0.1): int(minimap_height_pixel * 0.75),
                                      offset_minimap_pixel: offset_minimap_pixel + region_width_minimap_pixel,
                                      :],
                       (region_width_minimap_pixel, minimap_height_pixel))
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
        cv2.imshow(WINDOW_NAME_MINIMAP, cur_im_minimap)
        offset_bigmap_pixel = int(offset_meter * x_scale_bigmap)
        region_width_bigmap_pixel = int(region_width_meter * x_scale_bigmap)
        cv2.imshow(WINDOW_NAME_VISU, im_bigmap[:,
                                               offset_bigmap_pixel: offset_bigmap_pixel + region_width_bigmap_pixel,
                                               :])
        cv2.waitKey(16)

