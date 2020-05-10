

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

