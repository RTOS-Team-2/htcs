#ifndef HTCS_VEHICLE_STATE_H
#define HTCS_VEHICLE_STATE_H

#include "options.h"

#define LANE_CHANGE_MS 2000         // [millisec] time to spend between the two lanes

typedef enum Lanes {
    MERGE_LANE,
    MERGE_TO_TRAFFIC,
    TRAFFIC_LANE,
    TRAFFIC_TO_EXPRESS,
    EXPRESS_TO_TRAFFIC,
    EXPRESS_LANE
} Lane;

typedef enum AccelerationStates {
    MAINTAINING_SPEED,
    ACCELERATING,
    BRAKING
} AccelerationState;

typedef struct Attributes {
    double preferredSpeed;
    double maxSpeed;
    double acceleration;
    double brakingPower;
    double size;
} Attributes;

typedef struct State {
    Lane lane;
    double distanceTaken;
    double speed;
    unsigned laneChangeElapsed;
    AccelerationState accelerationState;
    Attributes attributes;
} State;

void initializeState(State* state, const Options* opts);

void adjustState(State* state, unsigned elapsedMs);

int attributesAndStateToString(State *state, char* attributesStr);

int stateToString(State* state, char* stateStr);

#endif //HTCS_VEHICLE_STATE_H
