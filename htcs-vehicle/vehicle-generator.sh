#!/usr/bin/env bash

echo "Initializing default values..."

if [ -z "${MQTT_PASSWORD}" ]; then echo "Missing MQTT_PASSWORD" && exit 1; fi

if [ -z "${MQTT_ADDRESS}" ]; then MQTT_ADDRESS="maqiatto.com"; fi
if [ -z "${MQTT_USERNAME}" ]; then MQTT_USERNAME="krisz.kern@gmail.com"; fi
if [ -z "${TOPIC}" ]; then TOPIC="krisz.kern@gmail.com/vehicles"; fi

GEN_INTERVAL_MIN=3  # in seconds
GEN_INTERVAL_MAX=10 # in seconds

PREF_SPEED_MIN=50
PREF_SPEED_MAX=160
MAX_SPEED_MIN=100
MAX_SPEED_MAX=280
ACCELERATION_MIN=3
ACCELERATION_MAX=14
BRAKING_POWER_MIN=3
BRAKING_POWER_MAX=14
SIZE_MIN=2
SIZE_MAX=10

LOG_FOLDER="logs/generation-$(date +"%Y%m%d%H%M%S")"
mkdir -p "${LOG_FOLDER}"

rand() {
  decimals=${3}
  zeros=$(printf "%0.s0" $(seq 1 "${decimals}"))

  min="${1}${zeros}"
  max="${2}${zeros}"

  echo "scale=${decimals};$(shuf -i "${min}"-"${max}" -n 1)/1${zeros}" | bc
}

echo "Starting generating random vehicles"
counter=0
while ${RUNNING}; do
  counter=$((counter + 1))

  CLIENT_ID=$(uuidgen)
  LOG_FILE=${LOG_FOLDER}/htcs_vehicle-${CLIENT_ID}.log

  LD_LIBRARY_PATH="${HOME}/Eclipse-Paho-MQTT-C-1.3.1-Linux/lib:${LD_LIBRARY_PATH}" \
  nohup \
  ./build/htcs_vehicle \
  --address "${MQTT_ADDRESS}" \
  --username "${MQTT_USERNAME}" \
  --password "${MQTT_PASSWORD}" \
  --clientId "${CLIENT_ID}" \
  --topic ${TOPIC} \
  --preferredSpeed "$(rand ${PREF_SPEED_MIN} ${PREF_SPEED_MAX} 3)" \
  --maxSpeed "$(rand ${MAX_SPEED_MIN} ${MAX_SPEED_MAX} 3)" \
  --acceleration "$(rand ${ACCELERATION_MIN} ${ACCELERATION_MAX} 3)" \
  --brakingPower "$(rand ${BRAKING_POWER_MIN} ${BRAKING_POWER_MAX} 3)" \
  --size "$(rand ${SIZE_MIN} ${SIZE_MAX} 3)" \
  &> "${LOG_FILE}" &

  echo "Generated vehicle no. ${counter} with PID: ${VEHICLE_PID}"

  SLEEP_TIME=$(rand ${GEN_INTERVAL_MIN} ${GEN_INTERVAL_MAX} 0)
  echo "Generating next vehicle in ${SLEEP_TIME} seconds"
  sleep "${SLEEP_TIME}"
done
