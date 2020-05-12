import os
import logging
from typing import Dict


# TODO: set C level maximum for position
# TODO: maybe create shared constants (enums) between c and python
local_cars = {}

config: Dict[str, any] = dict("".join(l.split()).split("=")
                              for l in open(os.path.dirname(os.path.abspath(__file__)) + "/connection.properties")
                              if not l.strip().startswith("#"))
config["position_bound"] = int(config["position_bound"])
config["quality_of_service"] = int(config["quality_of_service"])


class Lane(enum.Enum):
    MERGE_LANE = 0
    MERGE_TO_TRAFFIC = 1
    TRAFFIC_LANE = 2
    TRAFFIC_TO_EXPRESS = 3
    EXPRESS_TO_TRAFFIC = 4
    EXPRESS_LANE = 5


def set_logging_level():
    try:
        config_level = config["logging_level"].upper()
        logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                            level=config_level, datefmt='%Y-%m-%d %H:%M:%S')
    except ValueError:
        default_level = logging.WARNING
        logging.basicConfig(level=default_level)
        print(f"Default logging level set to: {logging.getLevelName(default_level)}")


set_logging_level()
