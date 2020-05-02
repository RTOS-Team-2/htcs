# Highway Traffic Control System (HTCS) Vehicle

This C project represents a simulated vehicle on a highway.

It communicates with an MQTT broker in a way that
it publishes its position, speed, etc.
and subscribes to commands from a controller
in order to safely navigate through the traffic.

## Linux install

1. [Download Eclipse Paho MQTT C](https://www.eclipse.org/downloads/download.php?file=/paho/1.4/Eclipse-Paho-MQTT-C-1.3.1-Linux.tar.gz&mirror_id=1099)
2. Extract it in your ${HOME} folder
3. `cd path/to/repo/htcs-vehicle`
4. Run build.sh

## Windows install

1. [Download Eclipse Paho MQTT C](https://www.eclipse.org/downloads/download.php?file=/paho/1.4/eclipse-paho-mqtt-c-win32-1.3.1.zip)
2. Unzip under %USERPROFILE%\eclipse-paho-mqtt-c-win32-1.3.1\
3. Add %USERPROFILE%\eclipse-paho-mqtt-c-win32-1.3.1\lib to PATH
4. Open the Project with Visual Studio
5. Run with Debug x86

## Usage

Example Linux invocation for [MaQiaTTo](https://maqiatto.com) connection:
```shell script
htcs-vehicle \
--address maqiatto.com \
--username krisz.kern@gmail.com \
--password ***** \
--client_id 1 \
--topic krisz.kern@gmail.com/vehicles
```

With Visual Studio on Windows you can set the
command line arguments in the Debugger section of the Project properties.

The program requires the following command line arguments to function properly:

* address
    * the address of the MQTT broker
    * format: `[protocol://]hostname[:port]`
* username
    * the username for the MQTT broker
* password
    * the password for the MQTT broker
* client_id
    * arbitrary string
    * identifies the vehicle
* topic
    * the topic base of vehicles
    * the vehicle will automatically subscribe to the topic:
    `<topic base>/<client_id>/command`
    it will receive commands from the controller on this topic
