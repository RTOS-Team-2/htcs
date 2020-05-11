from typing import List, Tuple, Dict, Callable


class CarSpecs:
    def __init__(self, specs):
        """
        :param specs[0]: preferred speed [m/sg
        :param specs[1]: max speed [m/s]
        :param specs[2]: acceleration [m/s^2]
        :param specs[3]: braking power [m/s^2]
        :param specs[4]: size of car [m] above 7.5 meter we are talking about a truck
        """
        self.preferred_speed = specs[0]
        self.max_speed = specs[1]
        self.acceleration = specs[2]
        self.braking_power = specs[3]
        self.size = specs[4]


class Car:
    def __init__(self, car_id, specs: CarSpecs, state):
        """
        see: htcs-vehicle/src/state.h
        :param state[0]: enum
        :param state[1]: distance taken along the single axis
        :param state[2]: speed [m/s]
        :param state[3]: enum
        :param specs: constant parameters of the car
        """
        self.id = car_id
        self.specs = specs
        self.lane = state[0]
        self.distance_taken = state[1]
        self.speed = state[2]
        self.acceleration_state = state[3]

    def update_state(self, state):
        self.lane = state[0]
        self.distance_taken = state[1]
        self.speed = state[2]
        self.acceleration_state = state[3]


class CarManager(dict):
    def __init__(self, *args):
        dict.__init__(self, args)

    def update_car(self, car_id, state):
        self[car_id].update_state(state)


# TODO: These should not be simple lists, but maybe something form bisect module
class DetailedCarTracker(dict):
    def __init__(self, *args):
        dict.__init__(self, args)
        # These will be all empty in all cases for now
        self.full_list = sorted(self.values(), key=lambda x: x.distance_taken)
        in_merge_lane = [car for car in self.full_list if car.lane == 0]
        from_merge_to_traffic_lane = [car for car in self.full_list if car.lane == 1]
        in_traffic_lane = [car for car in self.full_list if car.lane == 2]
        from_traffic_to_express_lane = [car for car in self.full_list if car.lane == 3]
        from_express_to_traffic_lane = [car for car in self.full_list if car.lane == 4]
        in_express_lane = [car for car in self.full_list if car.lane == 5]
        self.list_of_lanes = [in_merge_lane, from_merge_to_traffic_lane, in_traffic_lane,
                              from_traffic_to_express_lane, from_express_to_traffic_lane, in_express_lane]

    def __setitem__(self, key, value: Car):
        dict.__setitem__(self, key, value)
        self.put_into_full_list(value)
        self.put_into_lane_list(value)

    def put_into_full_list(self, value: Car):
        for index_with_bigger_value in range(0, len(self.full_list)):
            if self.full_list[index_with_bigger_value].distance_taken > value.distance_taken:
                self.full_list.insert(index_with_bigger_value - 1, value)
                return
        self.full_list.append(value)

    def put_into_lane_list(self, value: Car):
        for index_with_bigger_value in range(0, len(self.list_of_lanes[value.lane])):
            if self.list_of_lanes[value.lane][index_with_bigger_value].distance_taken > value.distance_taken:
                self.list_of_lanes[value.lane].insert(index_with_bigger_value - 1, value)
                return
        self.list_of_lanes[value.lane].append(value)

    # https://treyhunner.com/2019/04/why-you-shouldnt-inherit-from-list-and-dict-in-python/
    # TODO: here I left out the default part
    def pop(self, key):
        if key in self:
            value = self[key]
            del self[key]
            self.full_list.remove(value)
            self.list_of_lanes[value.lane].remove(value)
            return value
        else:
            return None

    def update_car(self, car_id, state):
        self[car_id].update_state(state)




