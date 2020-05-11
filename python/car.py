

class CarSpecs:
    def __init__(self, preferred_speed=0, max_speed=0, acceleration=0, braking_power=0, size=0):
        self.preferred_speed = preferred_speed
        self.max_speed = max_speed
        self.braking_power = braking_power
        self.acceleration = acceleration
        self.size = size


class Car:
    def __init__(self, car_id, specs: CarSpecs, distance_taken=0, lane=0, speed=0, acceleration_state=0):
        """
        :param distance_taken: distance taken along the single axis
        :param lane: ENUM TODO: what means what + typehint
        :param speed:
        :param acceleration_state: enum TODO: what means what + typehint
        :param specs: constant parameters of the car
        """

        self.id = car_id
        self.distance_taken = distance_taken
        self.lane = lane
        self.speed = speed
        self.acceleration_state = acceleration_state
        self.specs = specs

    def update_state(self, lane, distance_taken, speed, acceleration_state):
        self.lane = lane
        self.distance_taken = distance_taken
        self.speed = speed
        self.acceleration_state = acceleration_state

    def get_distance_taken(self):
        return self.distance_taken
    
    def get_follow_distance(self, safety_treshold=0.0):
        # follow_distance = az a táv ami alatt meg tud állni 0-ra az autó az aktuális sebességről
        # time to stop = speed / deceleration
        # distance traveled = aree under the function of speed(time)
        # which is a line from current speed at zero time, and zero speed at time to stop
        follow_distance = (self.speed / 2.0) * (self.speed / self.specs.braking_power)
        return (1 + safety_treshold) * follow_distance

    #HELP
    # distance taken while reaching target_speed from current_speed
    def distance_while_accelerating(current_speed, target_speed, acceleration, deceleration):
        _acceleration = 0
        if current_speed < target_speed:
            _acceleration = acceleration
        else:
            _acceleration = deceleration
        return 0
    
    def match_speed_now(self,other_car):
        #TODO not perfect, need a bit more calculations
        return (self.distance_taken + self.match_speed_distance(other_car.speed) + 
                other_car.get_follow_distance(safety_treshold = 0.0) <
                other_car.distance_taken)
        