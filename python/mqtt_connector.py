import ast
import uuid
import logging
import paho.mqtt.client as mqtt
from car import Car, CarSpecs
from typing import List, Tuple, Dict
from HTCSPythonUtil import config, local_cars

logger = logging.getLogger(__name__)

model_class = Car

client_1 = mqtt.Client("main_client_" + str(uuid.uuid4()))
state_client_pool: List[Tuple[mqtt.Client, Dict[str, int]]] = []
state_client_pool_size = 8

rr_counter = 0


def round_robin_state_subscribe(car_id: str):
    global rr_counter
    client, _car_ids_mids = state_client_pool[rr_counter]
    client.subscribe(topic=config["base_topic"] + "/" + car_id + "/state", qos=config["quality_of_service"])
    _car_ids_mids[car_id] = 0
    logger.debug(f"Car {car_id} joined client {rr_counter}")
    rr_counter += 1
    if rr_counter >= state_client_pool_size:
        rr_counter = 0


def unsubscribe_pool(car_id: str):
    for client, _car_ids_mids in state_client_pool:
        if car_id in _car_ids_mids.keys():
            _, _mid = client.unsubscribe(config["base_topic"] + "/" + car_id + "/state")
            logger.debug(f"Unsubscribing Car {car_id}, MID {_mid}")
            _car_ids_mids[car_id] = _mid
            return


def on_join_message(client, user_data, msg):
    message = msg.payload.decode("utf-8")
    car_id = msg.topic.split('/')[-2]
    car = local_cars.get(car_id)
    # non-empty message - joinTraffic
    if message:
        if car is None:
            [specs_part, state_part] = message.split('|')
            specs = ast.literal_eval(specs_part)
            state = ast.literal_eval(state_part)
            local_cars[car_id] = model_class(car_id, CarSpecs(specs), state)
            round_robin_state_subscribe(car_id)
        else:
            logger.warning(f"Car with already existing id ({car_id}) sent a join message")
    # empty message - exitTraffic
    elif car is not None:
        unsubscribe_pool(car_id)


def on_state_message(client, user_data, msg):
    car_id = msg.topic.split('/')[-2]
    car = local_cars.get(car_id)
    if car is None:
        logger.warning(f"Car with unrecognized id ({car_id}) sent a state message")
    else:
        state = ast.literal_eval(msg.payload.decode("utf-8"))
        local_cars[car_id].update_state(state)


def on_connect(client, user_data, flags, rc):
    if rc == 0:
        client.connected_flag = True
        logger.debug(f"Client {client} connected OK.")
    else:
        logger.error(f"Client {client} could not connect, return code = {rc}")
        exit(rc)


def on_disconnect(client, user_data, rc):
    logger.debug(f"Client {client} disconnected, return code = {rc}")


def remove_unsubscribed_car(client, _car_ids_mids, message_id):
    for car_id, mid in _car_ids_mids.items():
        if mid == message_id:
            local_cars.pop(car_id)
            _car_ids_mids.pop(car_id)
            logger.debug(f"Unsubscribed car {car_id}")
            return


# if you want to only subscribe to obituary messages, set the state_client_pool_size to 0
def setup_connector(_model_class=Car, on_terminate=None, _state_client_pool_size=8):
    global model_class, state_client_pool_size
    model_class = _model_class
    state_client_pool_size = _state_client_pool_size

    logger.info(f"Setting up main client and {state_client_pool_size} state clients")
    for i in range(state_client_pool_size):
        client_id = "state_client_" + str(i) + "-" + str(uuid.uuid4())
        state_client = mqtt.Client(client_id)

        car_ids_mids = {}
        state_client.user_data_set(car_ids_mids)

        state_client.username_pw_set(username=config["username"], password=config["password"])
        state_client.on_connect = on_connect
        state_client.on_message = on_state_message
        state_client.on_unsubscribe = remove_unsubscribed_car
        state_client.on_disconnect = on_disconnect

        state_client_pool.append((state_client, car_ids_mids))

        state_client.connect(config["address"])
        state_client.loop_start()

    client_1.username_pw_set(username=config["username"], password=config["password"])
    client_1.on_connect = on_connect
    client_1.on_disconnect = on_disconnect

    client_1.connect(config["address"])
    client_1.loop_start()
    if state_client_pool_size > 0:
        client_1.message_callback_add(config["base_topic"] + "/+/join", on_join_message)
        client_1.subscribe(topic=config["base_topic"] + "/+/join", qos=config["quality_of_service"])
    if on_terminate:
        client_1.message_callback_add(config["base_topic"] + "/obituary", on_terminate)
        client_1.subscribe(topic=config["base_topic"] + "/obituary", qos=config["quality_of_service"])


def cleanup_connector():
    client_1.loop_stop()
    for client, car_ids in state_client_pool:
        client.loop_stop()
