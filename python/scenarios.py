import os
import time
import random
import pickle
import bisect
import logging
import datetime
import itertools
import numpy as np
import mqtt_connector
from typing import List
from hungarian import Hungarian
from car import Car, CarManager, Lane, Command, effective_lanes


logger = logging.getLogger(__name__)
hun = Hungarian()
repo_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Scenario(object):

    def __init__(self, car: Car, neighbours: List[Car], command: Command = None):
        self.car: Car = car
        self.neighbours: List[Car] = neighbours
        self.command = command

    def __str__(self) -> str:
        return f"<Scenario - car: {self.car}, neighbours: {self.neighbours}, command: {self.command}>"

    def __repr__(self) -> str:
        return self.__str__()

    def compare(self, other: 'Scenario'):
        similarity = 0.0
        if self.car.lane != other.car.lane:
            return similarity

        len_1 = len(self.neighbours)
        len_2 = len(other.neighbours)
        if len_1 == 0 or len_2 == 0:
            if len_1 == 0 and len_2 == 0:
                return np.Inf
            return 0

        similarity_matrix = np.full((len_1, len_2), 0)
        for i, neighbour in enumerate(self.neighbours):
            for j, other_neighbour in enumerate(other.neighbours):
                similarity = self.compare_cars(neighbour, other_neighbour)
                if similarity > similarity_matrix[i, j]:
                    similarity_matrix[i, j] = similarity

        hun.calculate(similarity_matrix, is_profit_matrix=True)
        similarity += hun.get_total_potential() / (len_1 + len_2)
        return similarity

    def compare_cars(self, c1: Car, c2: Car):
        similarity = 0.0
        if c1.lane != c2.lane:
            return 0.0

        c1_diff = self.car.distance_taken - c1.distance_taken
        c2_diff = self.car.distance_taken - c2.distance_taken
        similarity += compare_stat(c1_diff, c2_diff)
        similarity += compare_stat(c1.speed, c2.speed)

        specs_weight = 0.2
        similarity += compare_stat(c1.specs.acceleration, c2.specs.acceleration, specs_weight)
        similarity += compare_stat(c1.specs.braking_power, c2.specs.braking_power, specs_weight)
        similarity += compare_stat(c1.specs.preferred_speed, c2.specs.preferred_speed, specs_weight)
        similarity += compare_stat(c1.specs.max_speed, c2.specs.max_speed, specs_weight)

        if c1.acceleration_state == c2.acceleration_state:
            similarity += 1

        return similarity


def compare_stat(stat_1: float, stat_2: float, weight: float = 1.0):
    if stat_1 == stat_2:
        return weight
    return weight / abs(stat_1 - stat_2)


def closest_neighbours(car: Car, car_list: List[Car]):
    neighbours = []
    car_list.sort(key=lambda c: c.lane)
    for lane, cars_in_lane in itertools.groupby(car_list, key=lambda c: c.lane):
        if (car.lane == Lane.MERGE_LANE and effective_lanes[lane] == Lane.EXPRESS_LANE) or \
                (car.lane == Lane.EXPRESS_LANE and effective_lanes[lane] == Lane.MERGE_LANE):
            continue

        cars_in_lane = list(cars_in_lane)
        cars_in_lane.sort(key=lambda c: c.distance_taken)

        distance_taken_list = [c.distance_taken for c in cars_in_lane]
        insert_idx = bisect.bisect_left(distance_taken_list, car.distance_taken)
        prev_car = cars_in_lane[insert_idx - 1] if insert_idx > 0 else None
        next_car = cars_in_lane[insert_idx + 1] if insert_idx < len(distance_taken_list) - 1 else None

        if prev_car is not None:
            neighbours.append(prev_car)
        if next_car is not None:
            neighbours.append(next_car)

    return neighbours


SIMILARITY_THRESHOLD = 6
scenarios: List[Scenario] = []


def looks_like_new_scenario(scenario: Scenario):
    for idx, sc in enumerate(scenarios):
        similarity = sc.compare(scenario)
        if similarity > SIMILARITY_THRESHOLD:
            logger.info(f"Similarity no. {idx} over threshold: {similarity} scenario_1: {scenario}, scenario_2: {sc}")
            return False
    return True


def gather_new_scenarios(sample_size: int = 5):
    if len(local_cars) < 5:
        logger.info("Not enough cars to gather new scenarios")
        return
    cars = list(local_cars.values())
    selected_cars = random.sample(cars, sample_size)
    new_scenarios = 0
    for car in selected_cars:
        scenario = Scenario(car, closest_neighbours(car, cars))
        logger.debug(f"Found scenario: {scenario}")
        if len(scenarios) == 0 or looks_like_new_scenario(scenario):
            new_scenarios = new_scenarios + 1
            scenarios.append(scenario)

    logger.info(f"Found {new_scenarios} new scenarios, total scenarios: {len(scenarios)}")
    return new_scenarios > 0


if __name__ == "__main__":
    local_cars: CarManager = CarManager()
    mqtt_connector.setup_connector(local_cars)
    found_new_scenarios = True

    while found_new_scenarios:
        time.sleep(3)
        found_new_scenarios = gather_new_scenarios()

    file_name = "scenario-" + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + ".dump"
    with open(os.path.join(repo_root_dir, "python", "logs", file_name), 'wb') as dump:
        pickle.dump(scenarios, dump)
