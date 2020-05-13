import cv2
import time
import logging
import numpy as np
import mqtt_connector
import visu_res as vis
from htcs_controller import give_command
from car import DetailedCarTracker, AccelerationState, Command, Lane

logger = logging.getLogger(__name__)
# view-dependent variables
offset_meter = 0
region_width_meter = vis.region_width_meter_start
offset_minimap_pixel = int(offset_meter * vis.x_scale_minimap)
region_width_minimap_pixel = int(region_width_meter * vis.x_scale_minimap)
offset_bigmap_pixel = int(offset_meter * vis.x_scale_bigmap)
region_width_bigmap_pixel = int(region_width_meter * vis.x_scale_bigmap)
current_detail_height = vis.detail_height
minimap_point_size = int(4 * vis.window_width / 2000)
# navigation variables
focused_car: vis.CarImage or None
x_slice_focused: slice
image_focused: np.ndarray
is_dragging = False
drag_start_x = 0
drag_start_offset = 0
# text management
text_size = 1 / (3000 / vis.window_width)
text_pixel_height = int(33 * text_size)
# some info
logger.info(f"Full length of the map is {vis.map_length_meter} m.")
logger.info(f"Current visible region is {vis.region_width_meter_start} m wide.")
logger.info(f"Press <w> key to zoom in, press <s> key to zoom out.")


def minimap_move(event, x, y, flags, param):
    global offset_minimap_pixel, drag_start_x, drag_start_offset, is_dragging, offset_meter, offset_bigmap_pixel
    if event == cv2.EVENT_LBUTTONDOWN:
        set_clicked_car(x, y)
        if offset_minimap_pixel <= x <= offset_minimap_pixel + region_width_minimap_pixel \
                and y < vis.minimap_height_pixel:
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


def set_clicked_car(x_click, y_click):
    global focused_car
    if y_click < vis.minimap_height_pixel + vis.black_region_height:
        if focused_car is not None:
            focused_car = None
        return
    y_real = (y_click - vis.minimap_height_pixel - vis.black_region_height) / \
        current_detail_height * vis.detail_height
    x_meter = x_click / vis.window_width * region_width_meter + offset_meter
    for c in local_cars.get_all():
        if c.is_in_region(offset_meter, region_width_meter):
            y_slice: slice = c.get_y_slice()
            if y_slice.start - 15 < y_real < y_slice.stop + 15:
                if c.distance_taken - c.specs.size - 10 < x_meter < c.distance_taken + 10:
                    focused_car = c
                    return
    focused_car = None


def on_terminate(client, userdata, message):
    car_id = message.payload.decode("utf-8")
    logger.debug(f"Obituary received for car: {car_id}")
    _car = local_cars.get(car_id)
    if _car is not None:
        _car.exploded = True


def follow_with_camera():
    global focused_car, x_slice_focused, image_focused, offset_meter, offset_minimap_pixel, offset_bigmap_pixel
    if focused_car is not None:
        if focused_car.distance_taken + region_width_meter / 2 > vis.map_length_meter - 5 \
                or focused_car.exploded:
            focused_car = None
        else:
            offset_meter = max(0, focused_car.distance_taken - region_width_meter / 2)
            x_slice_focused, image_focused = focused_car.get_x_slice_and_image(offset_meter, region_width_meter)
            offset_minimap_pixel = int(offset_meter * vis.x_scale_minimap)
            offset_bigmap_pixel = int(offset_meter * vis.x_scale_bigmap)


def put_on_title():
    # put title in cone
    canvas[vis.minimap_height_pixel: vis.minimap_height_pixel + vis.black_region_height, :, :] = vis.title
    cv2.fillConvexPoly(canvas, np.int32(((0, vis.minimap_height_pixel),
                                         (0, vis.minimap_height_pixel + vis.black_region_height),
                                         (offset_minimap_pixel, vis.minimap_height_pixel))), (0, 0, 0))
    cv2.fillConvexPoly(canvas, np.int32(((offset_minimap_pixel + region_width_minimap_pixel, vis.minimap_height_pixel),
                                         (vis.window_width, vis.minimap_height_pixel + vis.black_region_height),
                                         (vis.window_width, vis.minimap_height_pixel))), (0, 0, 0))


def set_minimap():
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


def draw_orange_lines():
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


def put_on_focused_car_stats():
    text_c = focused_car.text_color
    row_1_y = canvas.shape[0] - 5 - 3 * text_pixel_height
    row_2_y = canvas.shape[0] - 5 - 2 * text_pixel_height
    row_3_y = canvas.shape[0] - 5 - 1 * text_pixel_height
    row_4_y = canvas.shape[0] - 5
    cv2.putText(canvas, f"id={focused_car.id}", (5, row_1_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    speed_col_x = 5 + int(canvas.shape[1] * 0.07)
    cv2.putText(canvas, f"speed={focused_car.speed} [m/s]", (speed_col_x, row_2_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    cv2.putText(canvas, f"prefSpeed={focused_car.specs.preferred_speed}", (speed_col_x, row_3_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    cv2.putText(canvas, f"maxSpeed={focused_car.specs.max_speed}", (speed_col_x, row_4_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    acc_col_x = 5 + int(canvas.shape[1] * 0.21)
    cv2.putText(canvas, f"accState={AccelerationState(focused_car.acceleration_state).name}", (acc_col_x, row_1_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    cv2.putText(canvas, f"followDist={focused_car.follow_distance()}", (acc_col_x, row_2_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    cv2.putText(canvas, f"brakePower={focused_car.specs.braking_power} [m/s^2]", (acc_col_x, row_3_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    cv2.putText(canvas, f"acceleration={focused_car.specs.acceleration} [m/s^2]", (acc_col_x, row_4_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    lane_desc_x = 5 + int(canvas.shape[1] * 0.40)
    cv2.putText(canvas, f"eff.express", (lane_desc_x, row_2_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, (255, 255, 255), 2)
    cv2.putText(canvas, f"eff.traffic", (lane_desc_x, row_3_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, (255, 255, 255), 2)
    cv2.putText(canvas, f"eff.merge", (lane_desc_x, row_4_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, (255, 255, 255), 2)
    lane_behind_x = 5 + int(canvas.shape[1] * 0.47)
    d_e = focused_car.signed_distance_between(local_cars.car_directly_behind_in_effective_lane(focused_car, Lane.EXPRESS_LANE))
    d_t = focused_car.signed_distance_between(local_cars.car_directly_behind_in_effective_lane(focused_car, Lane.TRAFFIC_LANE))
    d_m = focused_car.signed_distance_between(local_cars.car_directly_behind_in_effective_lane(focused_car, Lane.MERGE_LANE))
    cv2.putText(canvas, f"dist. behind={np.floor(d_e)}", (lane_behind_x, row_2_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    cv2.putText(canvas, f"dist. behind={np.floor(d_t)}", (lane_behind_x, row_3_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    cv2.putText(canvas, f"dist. behind={np.floor(d_m)}", (lane_behind_x, row_4_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    lane_ahead_x = 5 + int(canvas.shape[1] * 0.60)
    d_e = focused_car.signed_distance_between(local_cars.car_directly_ahead_in_effective_lane(focused_car, Lane.EXPRESS_LANE))
    d_t = focused_car.signed_distance_between(local_cars.car_directly_ahead_in_effective_lane(focused_car, Lane.TRAFFIC_LANE))
    d_m = focused_car.signed_distance_between(local_cars.car_directly_ahead_in_effective_lane(focused_car, Lane.MERGE_LANE))
    cv2.putText(canvas, f"dist. ahead={np.floor(d_e)}", (lane_ahead_x, row_2_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    cv2.putText(canvas, f"dist. ahead={np.floor(d_t)}", (lane_ahead_x, row_3_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    cv2.putText(canvas, f"dist. ahead={np.floor(d_m)}", (lane_ahead_x, row_4_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    can_x = 5 + int(canvas.shape[1] * 0.75)
    cv2.putText(canvas, f"can overtake={local_cars.can_overtake(focused_car)}", (can_x, row_2_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    cv2.putText(canvas, f"can return={local_cars.can_return_to_traffic_lane(focused_car)}", (can_x, row_3_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)
    cv2.putText(canvas, f"can merge in={local_cars.can_merge_in(focused_car)}", (can_x, row_4_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_c, 2)


if __name__ == "__main__":
    local_cars = DetailedCarTracker()
    focused_car = None
    mqtt_connector.setup_connector(local_cars, vis.CarImage, on_terminate)

    cv2.namedWindow(vis.WINDOW_NAME)
    cv2.moveWindow(vis.WINDOW_NAME, 0, 0)
    cv2.setMouseCallback(vis.WINDOW_NAME, minimap_move)

    while cv2.getWindowProperty(vis.WINDOW_NAME, 0) >= 0:
        frame_start = time.time()
        canvas = np.zeros((vis.minimap_height_pixel + vis.black_region_height + current_detail_height + 5 + 4 * text_pixel_height,
                           vis.window_width, 3),
                          np.uint8)
        follow_with_camera()
        put_on_title()
        set_minimap()
        draw_orange_lines()
        # get current part of the map
        cur_im_detail = cv2.resize(vis.im_bigmap[:, offset_bigmap_pixel:offset_bigmap_pixel + region_width_bigmap_pixel, :],
                                   (vis.window_width, vis.detail_height),
                                   interpolation=cv2.INTER_NEAREST)
        # put on cars
        for car in local_cars.get_all():
            x, y = car.get_point_on_minimap()
            cv2.circle(canvas, (x, y), minimap_point_size, car.color, cv2.FILLED)
            if car.is_in_region(offset_meter, region_width_meter) and car != focused_car:
                x_slice_vis, car_im = car.get_x_slice_and_image(offset_meter, region_width_meter)
                cur_im_detail[car.get_y_slice(), x_slice_vis, :] = car_im
        if focused_car is not None:
            cur_im_detail[focused_car.get_y_slice(), x_slice_focused, :] = image_focused

        # set correct height
        canvas[vis.minimap_height_pixel + vis.black_region_height:
               vis.minimap_height_pixel + vis.black_region_height + current_detail_height, :, :] = \
            cv2.resize(cur_im_detail, (vis.window_width, current_detail_height))

        if focused_car is not None:
            put_on_focused_car_stats()
        # put frame time
        cv2.putText(canvas, f"FPS: {np.floor(1 / (time.time() - frame_start + 0.0001))}",
                    (5, canvas.shape[0] - 5), cv2.FONT_HERSHEY_SIMPLEX, text_size, (255, 255, 255), 2)

        cv2.imshow(vis.WINDOW_NAME, canvas)
        key = cv2.waitKey(2)
        if key == -1:
            continue
        elif key == ord('w'):
            region_width_meter = max(10, region_width_meter - 10)
            logger.info(f"New width of visible region is {region_width_meter} meters")
            update_zoom()
        elif key == ord('s'):
            region_width_meter = min(vis.map_length_meter, region_width_meter + 10)
            logger.info(f"New width of visible region is {region_width_meter} meters")
            update_zoom()
        elif key == ord('x') and focused_car is not None:
            focused_car.exploded = True
            give_command(focused_car, Command.TERMINATE)
        elif key == ord('c') and focused_car is not None:
            give_command(focused_car, Command.CHANGE_LANE)

    cv2.destroyAllWindows()
    mqtt_connector.cleanup_connector()

