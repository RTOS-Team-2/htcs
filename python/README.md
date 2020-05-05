# HTCS Controller and Visualizer

This Python project contains two separate programs, that share the abstract model of the Car object, and the MQTT connector.

## Notice

These programs will have to be started before any car is connected, since the join message needs to be handled, to create the car!

### HTCSPythonUtil

This file contains the mqtt connector. To use it, you have to call the get_connection_config() method, which returns a dictionary.
It reads the configuration from the connection.properties file, which should be created based on the template in the folder. Once the ocnfiguration is set, You can set up the mqtt client object, which is a global variable, and it handles the management of the local_cars dictionary, which is also a global variable. Import these two into your code, to use them. The client's loop have to be started / stopped inside your code. The connector's loop will run in a separate process, so the local_cars dictionary will be constantly updated in an asynchronous way.

Local car management assumes, that the payload is in a dictionary form, with the excpected keys!

## Contoller

## Visualizer

### Usage

Run the python script. Zoom with W / S keys, move with A / D keys. Exit from the program pressing X key. Do not close the opencv window.
(Will be improved). 

## Known issues

OpenCV's GUI (ismhow) fails to work on some linux distributions using Qt.

## TODO

We should defined a common protocol defining the meaning of state descriptors during communication, and the format of the payloads.
