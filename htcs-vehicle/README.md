# Highway Traffic Control System Vehicle

This C project represents a simulated vehicle on a highway.

It communicates with an MQTT broker in a way that
it publishes its position, speed, etc.
and subscribes to commands from a controller
in order to safely navigate through the traffic.

## Linux install

1. Have `gcc` installed
2. [Download Eclipse Paho MQTT C](https://www.eclipse.org/downloads/download.php?file=/paho/1.4/Eclipse-Paho-MQTT-C-1.3.1-Linux.tar.gz&mirror_id=1099)
3. Extract it in your ${HOME} folder
4. `cd path/to/repo/htcs-vehicle`
5. Run build.sh

## Windows install

1. [Download Eclipse Paho MQTT C](https://www.eclipse.org/downloads/download.php?file=/paho/1.4/eclipse-paho-mqtt-c-win32-1.3.1.zip)
2. Unzip under %USERPROFILE%\eclipse-paho-mqtt-c-win32-1.3.1\
3. Add %USERPROFILE%\eclipse-paho-mqtt-c-win32-1.3.1\lib to PATH
4. Optional
   1. Add two new local environment variables:
      1. VS_WINSDK_VERSION  : (Your installed Windows SDK version) (e.g.: 10.0.17763.0)
      2. VS_TOOLSET_VERSION : (Your installed Windows Platform tools version) (e.g.: v141)
   2. Or open and retarget the solution in Visual Studio to your own installed SDK version
5. Open the Project with Visual Studio
6. Run with Debug x86

## Usage

Example Linux invocation for [MaQiaTTo](https://maqiatto.com) connection:
```shell script
htcs-vehicle \
--address maqiatto.com \
--username krisz.kern@gmail.com \
--password ***** \
--clientId 1 \
--topic krisz.kern@gmail.com/vehicles \
--preferredSpeed 120.0 \
--maxSpeed 210.0 \
--acceleration 7.3 \
--brakingPower 4.5 \
--size 3.4
```

**The parameters above are all obligatory.**

With Visual Studio on Windows you can set the
command line arguments in the Debugger section of the Project properties.

The program requires the following command line arguments to function properly, defined in [options.h](src/options.h):
* **address**
    * the address of the MQTT broker
    * format: `[protocol://]hostname[:port]`
* **username**
    * the username for the MQTT broker
* **password**
    * the password for the MQTT broker
* **clientId**
    * arbitrary string
    * identifies the vehicle
* **topic**
    * the topic base of vehicles
* **preferredSpeed**
    * positive double
    * the preferred travel speed
    * unit: kilometres per hour
* **maxSpeed**
    * positive double
    * the maximum speed of the vehicle
    * unit: kilometres per hour
* **acceleration**
    * positive double
    * the constant acceleration of the vehicle
    * unit: the time it takes in seconds for the vehicle to reach 100 km/h from 0 km/h
* **brakingPower**
    * positive double
    * the constant braking power or deceleration of the vehicle
    * unit: the time it takes in seconds for the vehicle to reach 0 km/h from 100 km/h
* **size**
    * positive double
    * the length of the vehicle
    * unit: meter

The following parameters are optional:
* **updateFrequency**
    * positive integer
    * the rate of the state messages published
    * unit: milliseconds
    * default value: 100
* **startingLane**
    * positive integer
    * must be one of the Lane enumerator's values
        * 0 - MERGE_LANE
        * 1 - MERGE_TO_TRAFFIC
        * 2 - TRAFFIC_LANE
        * 3 - TRAFFIC_TO_EXPRESS
        * 4 - EXPRESS_TO_TRAFFIC
        * 5 - EXPRESS_LANE
    * default value: 0
* **startingDistance**
    * positive double
    * the distance where the vehicle will start its journey
    * unit: meter
    * default value: 0
* **startingSpeed**
    * positive double
    * the speed which the vehicle will start its journey
    * unit: kilometres per hour
    * default value: 50 km/h

## Description

At the start of the program, the vehicle will automatically subscribe to the topic:
`<topic base>/<client id>/command`  
It will receive commands from the controller on this topic, specified in [command.h](src/command.h).

After the subscription, the vehicle joins the highway traffic,
i.e. the vehicle publishes once to the topic:
`<topic base>/<client id>/join`  
It will send its parameters with this message:
* preferred speed
* maximum speed
* acceleration
* braking power
* size
* lane
* distanceTaken
* speed
* accelerationState

After joining, the vehicle starts to move forward with its starting parameters.
If the vehicle is in the express or merge lane at the start, it's accelerating by default.

The vehicle periodically publishes its state information to the topic:
`<topic base>/<client id>/state`  
The following variables are sent with this message:
* lane
* distanceTaken
* speed
* accelerationState
