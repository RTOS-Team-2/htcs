#!/usr/bin/env bash

echo "Initializing default values..."

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
while true; do
  counter=$((counter + 1))

  VEHICLE_PID=$(LOG_FOLDER=${LOG_FOLDER} \
  PREFERRED_SPEED=$(rand ${PREF_SPEED_MIN} ${PREF_SPEED_MAX} 3) \
  MAX_SPEED=$(rand ${MAX_SPEED_MIN} ${MAX_SPEED_MAX} 3) \
  ACCELERATION=$(rand ${ACCELERATION_MIN} ${ACCELERATION_MAX} 3) \
  BRAKING_POWER=$(rand ${BRAKING_POWER_MIN} ${BRAKING_POWER_MAX} 3) \
  SIZE=$(rand ${SIZE_MIN} ${SIZE_MAX} 3) \
  ./run.sh)

  echo "Generated vehicle no. ${counter} with PID: ${VEHICLE_PID}"

  SLEEP_TIME=$(rand ${GEN_INTERVAL_MIN} ${GEN_INTERVAL_MAX} 0)
  echo "Generating next vehicle in ${SLEEP_TIME} seconds"
  sleep "${SLEEP_TIME}"
done
