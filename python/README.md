# Highway Traffic Control System Python modules

The project's python code resides in this folder. The following modules can be used separately from each other,
they all represent a different feature of this simulation.

---
## Controller

_**TODO update this section**_

Very basic controller logic, it blindly commands all cars in the merge lane to switch to the traffic lane

Has to be started before any car is connected, just like the visualizer

Controlling start after STARTING_DELAY_SEC seconds (default is 10 seconds), so there is time to start the car client(s), can be modified in htcs-controller.py: line 8

---
## Visualizer

The [visualizer](visu.py) module lets the end-user experience the Highway Traffic Control System
in a dynamic and interactive way. It displays the map of the simulation in a top-down view where you
can see all the cars on the road and follow their journey through the traffic.

### Usage

Run the python script.
Move the camera by dragging the highlighted region on the minimap.
Zoom by pressing W / S keys. Exit from the program by closing the window.
Click a car on the map to focus the camera on it, and display it's state.

Try other keys for easter eggs. ;)

The window is not resizeable, it's width is set to match your display.

### Known issues

* OpenCV's GUI (imshow) fails to work on some linux distributions using Qt.  
*Workaround*: Do not use virtual environment, install OpenCV on your machine from apt:
`sudo apt-get install libopencv-dev`

---
## Generator

The [generator](generator.py) module endlessly generates new randomized vehicle processes by a realistic set of constraints.

It keeps checking its children and terminates the ones that are over their maximum life expectancy.

When terminating the generator program, it takes care, to send SIGTERM signals to all running vehicle processes.
The implementation is cross-platform, but assumes that you have the C project built in its default folder.

Archiving logs of the terminated vehicle processes are done periodically to save disk space.

---
## Terminator

The [terminator](terminator.py) module is a separate entity which basically represents the laws of nature.
In this simulation the vehicles don't know about each other, they cannot sense that they may have collided.

The terminator's most important job is to send the `TERMINATE` command to the vehicles that crashed into each other
*OR* reached the end of the road, thus ending their lifecycle.

This component was born because the controller may be biased to make this decision,
because it's goal is to prevent the collisions.

The terminator's secondary purpose is to publish an obituary about the vehicles it killed. The obituary contains
the vehicle's id, which should arrive to the subscribers a couple of cycles before the actual death notice
of the vehicle itself. This can be utilized with the `on_terminate` callback function.

---
## MQTT Connector

This is a connector designed to satisfy the needs of every module.
Each module creates their own connector.
The connector can asynchronously manage a dictionary-like class which has values or the Car class or its subclasses.
The connector has a main client and a number of additional clients.
The main client handles join messages, and upon a join message it subscribes a client to that vehicle's state topic,
in a round-robin manner. 

---
### HTCSPythonUtil

It reads the configuration from the connection.properties file, which should be created based on the
[template](template_connection.properties) in the folder. The MQTT connection's address and credentials are
essential for the other modules to be defined here.

The logging level is also by default with this util file.
