




# TODO: set C level maximum for position
POSITION_BOUND = 10000


class CarSpecs:
    def __init__(self, defaultSpeedFastLane, defaultSpeedSlowLane, maxBrake, maxAcc):
        self.defaultSpeedFastLane = defaultSpeedFastLane
        self.defaultSpeedSlowLane = defaultSpeedSlowLane
        self.maxBrake = maxBrake
        self.maxAcc = maxAcc


class Car:
    def __init__(self, pos, lane, speed, isBraking, specs: CarSpecs):
        """
        TODO: lane should have a distinct value for each entrance which changes to 1 when they enter the slowLane
        TODO: how do they accelerate in the entrance?
        TODO: we should decide where do we want ints, and where floats
        :param pos: position along a single axis since the cars only move along a single dimension
        :param lane: 0: fastLane 1: slowLane
        :param speed: current speed
        :param isBraking:
        :param specs: holds 4 car parameters: preferred speed in each lane, and max acceleration / deceleration
        """
        self.pos = pos
        self.lane = lane
        self.speed = speed
        self.isBraking = isBraking
        self.specs = specs

    @classmethod
    def forVisualization(cls, pos, lane):
        """
        Second constructor, since the visualization doesn't need the whole class
        """
        return cls(pos, lane, None, None, CarSpecs(None, None, None, None))

    def getRelativePosition(self):
        return self.pos / POSITION_BOUND





