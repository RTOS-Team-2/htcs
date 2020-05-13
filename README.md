# Highway Traffic Control System

This project is a simulation of highway scenarios, where multiple vehicles join and leave the traffic at different times.

The twist is that these vehicles are all controlled by a centralized puppetmaster, which makes sure that every vehicle
reaches its destination safely while also trying to maintain the preferred speed of each and every vehicle.

The project is a simulation, using the following model:

Each vehicle is represented by a separately running program, written in C, implemented for linux systems with real-time support and also for Windows. The vehicle is parametrized by command line arguements *link options*. The vehicle sends a join message, containing the specification of the car. The join message is retained, so every new subsriber will get it. The vehicle publishes a state message regularly (10 times a second), which conatins its current speed, acceleration state, lane and distance traveled. The vehicles continuously updates it's speed according to the acceleration status, and it's distance traveled, according to the speed. The vehicle can handle the following commands: MAINTAIN SPEED, BRAKE, ACCELERATE, CHANGE LANE, TERMINATE. Changing lane takes a fixed amount of time, during which the vehicle is between the two lanes.

Connection variables are to be set in a properties file. It is here, where the address and credentials of the central mqtt broker are specified. The generator will generate vehicles accordingly, and each python mqtt connector will connect to that broker.
