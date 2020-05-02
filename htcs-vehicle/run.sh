#!/usr/bin/env bash

if [ -z "${MAQIATTO_PASSWORD}" ]; then
  exit 1
fi

if [ -z "${BINARY_PATH}" ]; then
  BINARY_PATH="./build"
fi

if [ -z "${CLIENT_ID}" ]; then
  CLIENT_ID=$(uuidgen)
fi

if [ -z "${LOG_FOLDER}" ]; then
  mkdir -p logs
  LOG_FOLDER="logs"
fi

LOG_FILE=${LOG_FOLDER}/htcs_vehicle-${CLIENT_ID}-$(date +"%Y%m%d%H%M%S").log

LD_LIBRARY_PATH="${HOME}/Eclipse-Paho-MQTT-C-1.3.1-Linux/lib:${LD_LIBRARY_PATH}" \
${BINARY_PATH}/htcs_vehicle \
--address maqiatto.com \
--username krisz.kern@gmail.com \
--password "${MAQIATTO_PASSWORD}" \
--client_id "${CLIENT_ID}" \
--topic krisz.kern@gmail.com/vehicles \
&> "${LOG_FILE}" &

echo $!
