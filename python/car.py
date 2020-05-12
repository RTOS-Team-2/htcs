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
    
    def get_follow_distance(self, safety_factor=1.0):
        """
        Distance traveled while getting to a full stop from current speed
        :param safety_factor: returned value will be multiplied by this factor
        """
        # time to stop = speed / deceleration
        # distance traveled = aree under the function of speed(time)
        # which is a line from current speed at zero time, and zero speed at time to stop
        follow_distance = (self.speed / 2.0) * (self.speed / self.specs.braking_power)
        return safety_factor * follow_distance

    def distance_while_accelerating(self, target_speed):
        """
        Distance traveled while reaching target_speed from current_speed
        """
        # we calculate the area under the function of speed(time) which is a trapeziod
        if self.speed < target_speed:
            return (target_speed + self.speed) / 2 * (target_speed - self.speed) / self.specs.acceleration
        else:
            return (target_speed + self.speed) / 2 * (self.speed - target_speed) / self.specs.braking_power

    def match_speed_now(self,other_car):
        #TODO not perfect, need a bit more calculations
        return (self.distance_taken + self.match_speed_distance(other_car.speed) + 
                other_car.get_follow_distance(safety_treshold=1.0) <
                other_car.distance_taken)


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

# kik vannak tul kozel, és fékezniuk kell (vagy előzni)
# kik vannak a merge-ben és be kéne sávolniuk
# kik fékeznek, és kell-e még fékezniuk
# kik vannak az express lane ben, és vissza tudnak e menni a trafficba
class DetailedCarTracker(CarManager):
    def __init__(self):
        super().__init__()
        self.full_list = [] # TODO: typehint

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
                return
        self.full_list.append(value)

    def update_car(self, car_id, state):
        car = self[car_id]
        car.update_state(state)
        index_now = self.full_list.index(car)
        if index_now < len(self.full_list) - 1 and self.full_list[index_now + 1].distance_taken < car.distance_taken:
            self.full_list[index_now], self.full_list[index_now + 1] = \
                self.full_list[index_now + 1], car
        # we do not have to check the other swap, since the car could not move backwards

    def pop(self, key):
        for i in range(0, len(self.full_list)):
            if self.full_list[i].id == key:
                return self.full_list.pop(i)
        return None

    def generator_cars_in_merge_lane(self):
        for car in self.full_list:
            if car.lane == 0:
                yield car

    def generator_cars_in_traffic_lane(self):
        for car in self.full_list:
            if car.lane in [1, 2, 4]:
                yield car

    def generator_cars_in_express_lane(self):
        for car in self.full_list:
            if car.lane in [3, 5]:
                yield car

    def generator_cars_maintaining(self):
        for car in self.full_list:
            if car.acceleration_state == 0:
                yield car

    def generator_cars_accelerating(self):
        for car in self.full_list:
            if car.acceleration_state == 1:
                yield car

    def generator_cars_braking(self):
        for car in self.full_list:
            if car.acceleration_state == 2:
                yield car

    def generator_cars_in_front_of(self, car_in_focus: Car):
        for car in self.full_list:
            if car.distance_taken > car_in_focus.distance_taken:
                yield car

    def generator_cars_behind(self, car_in_focus: Car):
        for car in self.full_list:
            if car.distance_taken > car_in_focus.distance_taken:
                yield car

    def car_in_traffic_lane_directly_behind(self, car_in_focus: Car):
        index = self.full_list.index(car_in_focus) - 1
        while index >= 0:
            if self.full_list[index].lane in [1, 2, 4]:
                return self.full_list[index]
            index -= 1
        return None

    def car_in_express_lane_directly_behind(self, car_in_focus: Car):
        index = self.full_list.index(car_in_focus) - 1
        while index >= 0:
            if self.full_list[index].lane in [3, 5]:
                return self.full_list[index]
            index -= 1
        return None
