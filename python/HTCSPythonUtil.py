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


def set_logging_level():
    try:
        config_level = config["logging_level"].upper()
        logging.basicConfig(format='%(asctime)s %(name)s %(levelname)-8s %(message)s',
                            level=config_level, datefmt='%Y-%m-%d %H:%M:%S')
    except ValueError:
        default_level = logging.INFO
        logging.basicConfig(level=default_level)
        print(f"Default logging level set to: {default_level}")


set_logging_level()
