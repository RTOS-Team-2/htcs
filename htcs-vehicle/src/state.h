#ifndef HTCS_VEHICLE_STATE_H
#define HTCS_VEHICLE_STATE_H
#include "options.h"

#define STARTING_SPEED 13.8888889 // 50 km/h

typedef enum Lanes {
    MERGE_LANE,
    MERGE_TO_TRAFFIC_1,
    MERGE_TO_TRAFFIC_2,
    TRAFFIC_LANE,
    TRAFFIC_TO_EXPRESS_1,
    TRAFFIC_TO_EXPRESS_2,
    EXPRESS_TO_TRAFFIC_1,
    EXPRESS_TO_TRAFFIC_2,
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
    AccelerationState accelerationState;
    Attributes attributes;
} State;

void initializeState(State* state, const Options* opts);

void adjustState(State* state, unsigned elapsedMs);

int attributesToString(Attributes* attributes, char* attributesStr);

int stateToString(State* state, char* stateStr);

#endif //HTCS_VEHICLE_STATE_H
