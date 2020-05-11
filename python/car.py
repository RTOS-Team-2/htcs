

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

    def update_state(self, lane, distance_taken, speed, acceleration_state):
        self.lane = lane
        self.distance_taken = distance_taken
        self.speed = speed
        self.acceleration_state = acceleration_state
    
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
        