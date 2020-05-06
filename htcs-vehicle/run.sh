#!/usr/bin/env bash

# default mqtt
if [ -z "${MQTT_ADDRESS}" ]; then MQTT_ADDRESS="maqiatto.com"; fi
if [ -z "${MQTT_USERNAME}" ]; then MQTT_USERNAME="krisz.kern@gmail.com"; fi
if [ -z "${MQTT_PASSWORD}" ]; then echo "Missing MQTT_PASSWORD" && exit 1; fi
if [ -z "${CLIENT_ID}" ]; then CLIENT_ID=$(uuidgen); fi
if [ -z "${TOPIC}" ]; then TOPIC="krisz.kern@gmail.com/vehicles"; fi

if [ -z "${BINARY_PATH}" ]; then BINARY_PATH="./build"; fi
if [ -z "${LOG_FOLDER}" ]; then mkdir -p logs && LOG_FOLDER="logs"; fi
LOG_FILE=${LOG_FOLDER}/htcs_vehicle-${CLIENT_ID}-$(date +"%Y%m%d%H%M%S").log

# default vehicle parameters
if [ -z "${PREFERRED_SPEED}" ]; then PREFERRED_SPEED="120.0"; fi
if [ -z "${MAX_SPEED}" ]; then MAX_SPEED="210.0"; fi
if [ -z "${ACCELERATION}" ]; then ACCELERATION="7.3"; fi
if [ -z "${BRAKING_POWER}" ]; then BRAKING_POWER="4.5"; fi
if [ -z "${SIZE}" ]; then SIZE="3.4"; fi

LD_LIBRARY_PATH="${HOME}/Eclipse-Paho-MQTT-C-1.3.1-Linux/lib:${LD_LIBRARY_PATH}" \
${BINARY_PATH}/htcs_vehicle \
--address "${MQTT_ADDRESS}" \
--username "${MQTT_USERNAME}" \
--password "${MQTT_PASSWORD}" \
--clientId "${CLIENT_ID}" \
--topic ${TOPIC} \
--preferredSpeed "${PREFERRED_SPEED}" \
--maxSpeed "${MAX_SPEED}" \
--acceleration "${ACCELERATION}" \
--brakingPower "${BRAKING_POWER}" \
--size "${SIZE}" \
&> "${LOG_FILE}" &
# start in background with &
# $! is the PID of the most recent background command
echo $!
