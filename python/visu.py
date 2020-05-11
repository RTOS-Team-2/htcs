import cv2
import logging
import threading
import numpy as np
import mqtt_connector
import visu_res as vis
from HTCSPythonUtil import local_cars


logger = logging.getLogger(__name__)
# view-dependent variables
offset_meter = 0
region_width_meter = vis.region_width_meter_start
offset_minimap_pixel = int(offset_meter * vis.x_scale_minimap)
region_width_minimap_pixel = int(region_width_meter * vis.x_scale_minimap)
offset_bigmap_pixel = int(offset_meter * vis.x_scale_bigmap)
region_width_bigmap_pixel = int(region_width_meter * vis.x_scale_bigmap)
current_detail_height = vis.detail_height
# navigation variables
is_dragging = False
drag_start_x = 0
drag_start_offset = 0
logger.info(f"Full length of the map is {vis.map_length_meter} m.")
logger.info(f"Current visible region is {vis.region_width_meter_start} m wide.")
logger.info(f"Press <w> key to zoom in, press <s> key to zoom out.")


def minimap_move(event, x, y, flags, param):
    global offset_minimap_pixel, drag_start_x, drag_start_offset, is_dragging, offset_meter, offset_bigmap_pixel
    if event == cv2.EVENT_LBUTTONDOWN and \
            offset_minimap_pixel <= x <= offset_minimap_pixel + region_width_minimap_pixel and \
            y < vis.minimap_height_pixel:
        drag_start_x = x
        drag_start_offset = offset_minimap_pixel
        is_dragging = True
    elif event == cv2.EVENT_MOUSEMOVE and is_dragging:
        offset_minimap_pixel = max(0, min(drag_start_offset + x - drag_start_x,
                                          vis.minimap_length_pixel - region_width_minimap_pixel))
        offset_meter = offset_minimap_pixel / vis.x_scale_minimap
        offset_bigmap_pixel = int(offset_meter * vis.x_scale_bigmap)
    elif event == cv2.EVENT_LBUTTONUP:
        is_dragging = False
    # elif event == cv2.EVENT_MOUSEWHEEL:
    #     print(param)


def update_zoom():
    global current_detail_height, offset_minimap_pixel, offset_bigmap_pixel, offset_meter, region_width_meter, region_width_minimap_pixel, region_width_bigmap_pixel
    current_detail_height = int(vis.window_width * vis.map_height_meter / region_width_meter)
    if offset_meter + region_width_meter >= vis.map_length_meter:
        offset_meter -= offset_meter + region_width_meter - vis.map_length_meter
        offset_minimap_pixel = int(offset_meter * vis.x_scale_minimap)
        offset_bigmap_pixel = int(offset_meter * vis.x_scale_bigmap)
    region_width_minimap_pixel = int(region_width_meter * vis.x_scale_minimap)
    region_width_bigmap_pixel = int(region_width_meter * vis.x_scale_bigmap)


def terminator_callback(car_ids):
    logger.info(f"Terminated callback called: {car_ids}")
    car1 = local_cars.get(car_ids[0])
    car2 = local_cars.get(car_ids[1])
    if car1 is not None:
        car1.exploded = True
    if car2 is not None:
        car2.exploded = True


if __name__ == "__main__":
    mqtt_connector.setup_connector(vis.CarImage, terminator_callback)
    lock = threading.Lock()

    cv2.namedWindow(vis.WINDOW_NAME)
    cv2.moveWindow(vis.WINDOW_NAME, 0, 0)
    cv2.setMouseCallback(vis.WINDOW_NAME, minimap_move)

    while cv2.getWindowProperty(vis.WINDOW_NAME, 0) >= 0:
        canvas = np.zeros((vis.minimap_height_pixel + vis.black_region_height + current_detail_height,
                           vis.window_width, 3),
                          np.uint8)
        # put title in cone
        canvas[vis.minimap_height_pixel: vis.minimap_height_pixel + vis.black_region_height, :, :] = vis.title
        cv2.fillConvexPoly(canvas, np.int32(((0, vis.minimap_height_pixel),
                                             (0, vis.minimap_height_pixel + vis.black_region_height),
                                             (offset_minimap_pixel, vis.minimap_height_pixel))), (0, 0, 0))
        cv2.fillConvexPoly(canvas, np.int32(((offset_minimap_pixel + region_width_minimap_pixel, vis.minimap_height_pixel),
                                             (vis.window_width, vis.minimap_height_pixel + vis.black_region_height),
                                             (vis.window_width, vis.minimap_height_pixel))), (0, 0, 0))
        # get current part of the map
        cur_im_detail = cv2.resize(vis.im_bigmap[:, offset_bigmap_pixel:offset_bigmap_pixel + region_width_bigmap_pixel, :],
                                   (vis.window_width, vis.detail_height),
                                   interpolation=cv2.INTER_NEAREST)
        # gray out
        canvas[:vis.minimap_height_pixel, : offset_minimap_pixel, :] = \
            (vis.im_minimap[:, : offset_minimap_pixel, :] * 0.6).astype(np.int32)
        canvas[:vis.minimap_height_pixel, offset_minimap_pixel + region_width_minimap_pixel:, :] = \
            (vis.im_minimap[:, offset_minimap_pixel + region_width_minimap_pixel:, :] * 0.6).astype(np.int32)
        # zoom in
        canvas[:vis.minimap_height_pixel, offset_minimap_pixel: offset_minimap_pixel + region_width_minimap_pixel, :] = \
            cv2.resize(vis.im_minimap[int(vis.minimap_height_pixel * 0.05): int(vis.minimap_height_pixel * 0.94),
                                      offset_minimap_pixel: offset_minimap_pixel + region_width_minimap_pixel, :],
                       (region_width_minimap_pixel, vis.minimap_height_pixel))
        # put on cars
        with lock:
            cars = list(local_cars.values())
        for car in cars:
            x, y = car.get_point_on_minimap()
            cv2.circle(canvas, (x, y), 4, car.color, cv2.FILLED)
            if car.is_in_region(offset_meter, region_width_meter):
                x_slice_vis, car_im = car.get_x_slice_and_image(offset_meter, region_width_meter)
                cur_im_detail[car.get_y_slice(), x_slice_vis, :] = car_im
        # orange lines
        cv2.line(canvas,
                 (offset_minimap_pixel, 0),
                 (offset_minimap_pixel, vis.minimap_height_pixel),
                 (0, 211, 255),
                 3)
        cv2.line(canvas,
                 (offset_minimap_pixel + region_width_minimap_pixel, 0),
                 (offset_minimap_pixel + region_width_minimap_pixel, vis.minimap_height_pixel),
                 (0, 211, 255),
                 3)
        cv2.line(canvas,
                 (offset_minimap_pixel, vis.minimap_height_pixel),
                 (0, vis.minimap_height_pixel + vis.black_region_height),
                 (0, 211, 255),
                 3)
        cv2.line(canvas,
                 (offset_minimap_pixel + region_width_minimap_pixel, vis.minimap_height_pixel),
                 (vis.window_width, vis.minimap_height_pixel + vis.black_region_height),
                 (0, 211, 255),
                 3)
        # set correct height
        canvas[vis.minimap_height_pixel + vis.black_region_height:, :, :] = \
            cv2.resize(cur_im_detail, (vis.window_width, current_detail_height))

        cv2.imshow(vis.WINDOW_NAME, canvas)
        key = cv2.waitKey(1)
        if key == ord('w'):
            region_width_meter = max(10, region_width_meter - 10)
            update_zoom()
        elif key == ord('s'):
            region_width_meter = min(vis.map_length_meter, region_width_meter + 10)
            update_zoom()

    cv2.destroyAllWindows()
    mqtt_connector.cleanup_connector()

