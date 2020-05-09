import os
from typing import Dict


# TODO: set C level maximum for position
# TODO: maybe create shared constants (enums) between c and python
local_cars = {}

config: Dict[str, any] = dict("".join(l.split()).split("=")
                              for l in open(os.path.dirname(os.path.abspath(__file__)) + "/connection.properties")
                              if not l.strip().startswith("#"))
config["position_bound"] = int(config["position_bound"])
config["quality_of_service"] = int(config["quality_of_service"])

