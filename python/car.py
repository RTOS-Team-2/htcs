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
        self.lists_in_lanes = [in_merge_lane, from_merge_to_traffic_lane, in_traffic_lane,
                               from_traffic_to_express_lane, from_express_to_traffic_lane, in_express_lane]
        are_maintaining = [car for car in self.full_list if car.acceleration_state == 0]
        are_accelerating = [car for car in self.full_list if car.acceleration_state == 1]
        are_braking = [car for car in self.full_list if car.acceleration_state == 2]
        self.list_of_acceleration_states = [are_maintaining, are_accelerating, are_braking]

    def __setitem__(self, key, value: Car):
        dict.__setitem__(self, key, value)
        self.put_into_full_list(value)
        self.put_into_lane_list(value)

    def put_into_full_list(self, value: Car):
        for index_with_bigger_dist in range(0, len(self.full_list)):
            if self.full_list[index_with_bigger_dist].distance_taken > value.distance_taken:
                self.full_list.insert(index_with_bigger_dist - 1, value)
                return
        self.full_list.append(value)

    def put_into_lane_list(self, value: Car):
        for index_with_bigger_dist in range(0, len(self.lists_in_lanes[value.lane])):
            if self.lists_in_lanes[value.lane][index_with_bigger_dist].distance_taken > value.distance_taken:
                self.lists_in_lanes[value.lane].insert(index_with_bigger_dist - 1, value)
                return
        self.lists_in_lanes[value.lane].append(value)

    def update_car(self, car_id, state):
        car = self[car_id]
        lane_old = car.lane
        acceleration_state_old = car.acceleration_state

        car.update_state(state)

        index_now = self.full_list.index(car)
        if index_now < len(self.full_list) - 1 and self.full_list[index_now + 1].distance_taken < car.distance_taken:
            self.full_list[index_now], self.full_list[index_now + 1] = \
                self.full_list[index_now + 1], car
        # we do not have to check the other swap, since the car could not move backwards
        if lane_old != car.lane:
            self.lists_in_lanes[lane_old].remove(car)
            self.put_into_lane_list(car)
        # but in this case we have to check in the other list separately
        else:
            index_now = self.lists_in_lanes[car.lane].index(car)
            if index_now < len(self.lists_in_lanes[car.lane]) - 1 and \
               self.lists_in_lanes[car.lane][index_now + 1].distance_taken < car.distance_taken:
                self.lists_in_lanes[car.lane][index_now], self.lists_in_lanes[car.lane][index_now + 1] = \
                    self.lists_in_lanes[car.lane][index_now + 1], car

        if acceleration_state_old != car.acceleration_state:
            self.list_of_acceleration_states[acceleration_state_old].remove(car)
            self.list_of_acceleration_states[car.acceleration_state].append(car)

    # https://treyhunner.com/2019/04/why-you-shouldnt-inherit-from-list-and-dict-in-python/
    # TODO: here I left out the default part
    def pop(self, key):
        if key in self:
            value = self[key]
            del self[key]
            self.full_list.remove(value)
            self.lists_in_lanes[value.lane].remove(value)
            return value
        else:
            return None

    def get_car_in_front_of(self, car: Car):
        index_in_lane = self.lists_in_lanes[car.lane].index(car)
        if index_in_lane < len(self.lists_in_lanes[car.lane]) - 1:
            return self.lists_in_lanes[car.lane][index_in_lane + 1]
        else:
            return None

    def get_car_to_cut(self, car_about_to_switch: Car, destination_lane):
        for index_with_smaller_dist in range(len(self.lists_in_lanes[destination_lane]) - 1, -1, -1):
            if self.lists_in_lanes[destination_lane][index_with_smaller_dist]. \
                    distance_taken < car_about_to_switch.distance_taken:
                return self.lists_in_lanes[destination_lane][index_with_smaller_dist]
        return None

    def there_is_a_car_next_to(self, car: Car, destination_lane):
        # Distance taken is the distance at the very front of the vehicle
        index = self.full_list.index(car)
        go_on = True
        index_examined = index - 1
        while index_examined >= 0 and go_on:
            if car.distance_taken - car.specs.size <= self.full_list[index_examined].distance_taken:
                if self.full_list[index_examined].lane == destination_lane:
                    return True
                else:
                    index_examined -= 1
            else:
                go_on = False
        go_on = True
        index_examined = index + 1
        while index_examined < len(self.full_list) and go_on:
            if car.distance_taken >= \
                    self.full_list[index_examined].distance_taken - self.full_list[index_examined].specs.size:
                if self.full_list[index_examined].lane == destination_lane:
                    return True
                else:
                    index_examined += 1
            else:
                go_on = False
