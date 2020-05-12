import threading
from typing import List


effective_lanes = [0, 1, 1, 2, 1, 2]


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
    
    def follow_distance(self, safety_factor=1.0):
        """
        Distance traveled while getting to a full stop from current speed
        :param safety_factor: returned value will be multiplied by this factor
        """
        # time to stop = speed / deceleration
        # distance traveled = aree under the function of speed(time)
        # which is a line from current speed at zero time, and zero speed at time to stop
        follow_distance = (self.speed / 2.0) * (self.speed / self.specs.braking_power)
        return safety_factor * follow_distance

    def distance_while_reaching_speed(self, target_speed):
        """
        Distance traveled while reaching target_speed from current_speed
        """
        # we calculate the area under the function of speed(time) which is a trapeziod
        if self.speed < target_speed:
            return (target_speed + self.speed) / 2 * (target_speed - self.speed) / self.specs.acceleration
        else:
            return (target_speed + self.speed) / 2 * (self.speed - target_speed) / self.specs.braking_power

    def effective_lane(self):
        return effective_lanes[self.lane]


# These classes simulate a dictionary
class CarManager:
    def __init__(self):
        self.as_dict = {}

    def __setitem__(self, key, value: Car):
        self.as_dict[key] = value

    def __getitem__(self, key):
        return self.as_dict[key]

    def pop(self, key):
        return self.as_dict.pop(key)

    def get(self, key):
        return self.as_dict.get(key)

    def values(self):
        return self.as_dict.values()

    def update_car(self, car_id, state):
        self.as_dict[car_id].update_state(state)


class DetailedCarTracker(CarManager):
    def __init__(self):
        super().__init__()
        self.full_list: List[Car] = []
        self.lock = threading.Lock()

    def __getitem__(self, key):
        for car in self.full_list:
            if car.id == key:
                return car
        raise KeyError

    def get(self, key):
        for car in self.full_list:
            if car.id == key:
                return car
        return None

    def __setitem__(self, key, value: Car):
        self.put_into_full_list(value)

    def put_into_full_list(self, value: Car):
        for index_with_bigger_dist in range(0, len(self.full_list)):
            if self.full_list[index_with_bigger_dist].distance_taken > value.distance_taken:
                self.full_list.insert(index_with_bigger_dist, value)
                print("inserted to index", index_with_bigger_dist)
                return
        self.full_list.append(value)

    def update_car(self, car_id, state):
        car = self[car_id]
        car.update_state(state)
        index_now = self.full_list.index(car)
        if index_now < len(self.full_list) - 1 and self.full_list[index_now + 1].distance_taken < car.distance_taken:
            with self.lock:
                self.full_list[index_now], self.full_list[index_now + 1] = \
                    self.full_list[index_now + 1], self.full_list[index_now]
            print("SWAPPP !")
        # we do not have to check the other swap, since the car could not have moved backwards

    def pop(self, key):
        for i in range(0, len(self.full_list)):
            if self.full_list[i].id == key:
                return self.full_list.pop(i)
        return None

    def get_all(self):
        # this is a new list of object pointers
        with self.lock:
            return [car for car in self.full_list]

    def car_directly_behind_in_lane(self, car_in_focus: Car, lane):
        index = self.full_list.index(car_in_focus) - 1
        while index >= 0:
            if self.full_list[index].effective_lane() == lane:
                return self.full_list[index]
            index -= 1
        return None

    def car_directly_ahead_in_effective_lane(self, car_in_focus: Car, lane):
        index = self.full_list.index(car_in_focus) + 1
        while index < len(self.full_list):
            if self.full_list[index].effective_lane() == lane:
                return self.full_list[index]
            index += 1
        return None

    def can_overtake(self, car_in_focus: Car):
        if car_in_focus.lane != 2:
            return False
        car_ahead_if_overtake = self.car_directly_ahead_in_effective_lane(car_in_focus, 2)
        # if road ahead in express lane is not clear
        if car_ahead_if_overtake is not None:
            # if there is a faster vehicle there, we only check not to hit it immediately
            if car_ahead_if_overtake.speed > car_in_focus.speed:
                if car_ahead_if_overtake.distance_taken - car_ahead_if_overtake.specs.size < car_in_focus.distance_taken:
                    return False
            # else we check if we can brake while overtaking and not hit that
            else:
                if car_in_focus.distance_while_reaching_speed(car_ahead_if_overtake.speed) > \
                   car_ahead_if_overtake.distance_taken - car_in_focus.distance_taken:
                    return False
        car_behind_if_overtake = self.car_directly_behind_in_lane(car_in_focus, 2)
        # if we cut someone's path
        if car_behind_if_overtake is not None \
                and car_behind_if_overtake.distance_while_reaching_speed(car_in_focus.speed) > \
                car_in_focus.distance_taken - car_behind_if_overtake.distance_taken:
            return False
        return True

    def can_merge_in(self, car_in_focus: Car):
        if car_in_focus.lane != 0:
            return False
        car_ahead_if_merge_in = self.car_directly_ahead_in_effective_lane(car_in_focus, 1)
        # if road ahead in express lane is not clear
        if car_ahead_if_merge_in is not None:
            # if there is a faster vehicle there, we only check not to hit it immediately
            if car_ahead_if_merge_in.speed > car_in_focus.speed:
                if car_ahead_if_merge_in.distance_taken - car_ahead_if_merge_in.specs.size < car_in_focus.distance_taken:
                    return False
            # else we check if we can brake while merging in
            else:
                if car_in_focus.distance_while_reaching_speed(car_ahead_if_merge_in.speed) > \
                   car_ahead_if_merge_in.distance_taken - car_in_focus.distance_taken:
                    return False
        car_behind_if_merge_in = self.car_directly_behind_in_lane(car_in_focus, 1)
        # if we cut someone's path
        if car_behind_if_merge_in is not None \
                and car_behind_if_merge_in.distance_while_reaching_speed(car_in_focus.speed) * 2 > \
                car_in_focus.distance_taken - car_behind_if_merge_in.distance_taken:
            return False
        return True

    def can_return_to_traffic_lane(self, car_in_focus: Car):
        if car_in_focus.lane != 5:
            return False
        car_ahead_if_return = self.car_directly_ahead_in_effective_lane(car_in_focus, 1)
        if car_ahead_if_return is not None \
           and car_ahead_if_return.speed < car_in_focus.specs.preferred_speed \
           and car_ahead_if_return.distance_taken - car_in_focus.distance_taken < 300:
            return False
        return True
