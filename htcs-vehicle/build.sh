#!/usr/bin/env bash

rm -rf build
mkdir -p build

gcc src/*.c \
-o build/htcs_vehicle \
-I"${HOME}/Eclipse-Paho-MQTT-C-1.3.1-Linux/include" \
-L"${HOME}/Eclipse-Paho-MQTT-C-1.3.1-Linux/lib" \
-lpaho-mqtt3as \
-lrt
