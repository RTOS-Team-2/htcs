# Highway Traffic Control System

## Summary

This project is a simulation of highway scenarios, where multiple vehicles join and leave the traffic at different times.

The twist is that these vehicles are all controlled by a centralized puppet master, which makes sure that every vehicle
reaches its destination safely while also trying to maintain the preferred speed of each and every vehicle.

## Modules

Each vehicle is represented by a separately running program, written in C,
implemented for Linux systems with real-time support and also for Windows.

See the [readme file](htcs-vehicle/README.md) of the vehicle module for more information.

The project contains a number of different, separately usable python modules.
These are the **visualization**, the **controller**, the **generator** and the **terminator** modules.

See the [readme file](python/README.md) of the python modules for more information.

