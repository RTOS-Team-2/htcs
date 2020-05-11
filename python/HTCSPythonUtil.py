import os
import logging
from typing import Dict
from car import CarManager, DetailedCarTracker


local_cars = DetailedCarTracker()

config: Dict[str, any] = dict("".join(l.split()).split("=")
                              for l in open(os.path.dirname(os.path.abspath(__file__)) + "/connection.properties")
                              if not l.strip().startswith("#"))
config["position_bound"] = int(config["position_bound"])
config["quality_of_service"] = int(config["quality_of_service"])


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
