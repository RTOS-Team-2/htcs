# Highway Traffic Control System

This project's python code resides in this folder. The following modules can be used separately from each other,
they all represent a different feature of this simulation.

## Controller

_**TODO update this section**_

Very basic controller logic, it blindly commands all cars in the merge lane to switch to the traffic lane

Has to be started before any car is connected, just like the visualizer

Controlling start after STARTING_DELAY_SEC seconds (default is 10 seconds), so there is time to start the car client(s), can be modified in htcs-controller.py: line 8


## Visualizer

_**TODO update this section**_

### Usage

Run the python script. Zoom with W / S keys, move with A / D keys. Exit from the program pressing X key. Do not close the opencv window.
(Will be improved). 

### Known issues

OpenCV's GUI (imshow) fails to work on some linux distributions using Qt.

Workaround:
Do not use virtual environment, install OpenCV on your machine from apt:
`sudo apt-get install libopencv-dev`


## Generator

The [generator](generator.py) module endlessly generates new randomized vehicle processes by a realistic set of constraints.

It keeps checking its children and terminates the ones that are over their maximum life expectancy.

Archiving logs of the terminated vehicle processes are done periodically.

## Terminator

The [terminator](terminator.py) module is a separate entity which basically represents the laws of nature.
In this simulation the vehicles don't know about each other, they cannot sense that they may have collided.

The terminator's most important job is to send the `TERMINATE` command to the vehicles that crashed into each other
OR reached the end of the road, thus ending their lifecycle.

This component was born because the controller may be biased to make this decision,
because it's goal is to prevent the collisions.

The terminator's secondary purpose is to publish an obituary about the vehicles it killed. The obituary contains
the vehicle's id, which should arrive to the subscribers a couple of cycles before the actual death notice
of the vehicle itself. This can be utilized with the `on_terminate` callback function.

### HTCSPythonUtil

It reads the configuration from the connection.properties file, which should be created based on the
[template](template_connection.properties) in the folder. The logging level is also by default with this util file.

## TODO

We should define a common protocol defining the meaning of state descriptors during communication, and the format of the payloads.
