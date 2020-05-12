import os
import ast
import logging


config ={}
with open(os.path.dirname(os.path.abspath(__file__)) + "/connection.properties") as config_file:
    for line in config_file:
        if not line.strip().startswith('#'):
            [key, value_part] = "".join(line.split()).split("=")
            value_part = value_part.split("#")[0].strip()
            try:
                value = ast.literal_eval(value_part)
            except (ValueError, SyntaxError, NameError):
                value = value_part
            config[key] = value


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
