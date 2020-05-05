#include "state.h"
#include <stdio.h>

void initializeState(State* state, const Options* opts) {
    state->lane = MERGE_LANE;
    state->distanceTaken = 0.0;
    state->speed = STARTING_SPEED;
    state->laneChangeElapsed = 0;
    state->accelerationState = MAINTAINING_SPEED;

    state->attributes.preferredSpeed = opts->preferredSpeed / 3.6;
    state->attributes.maxSpeed = opts->maxSpeed / 3.6;
    state->attributes.acceleration = 1 / (0.036 * opts->acceleration);
    state->attributes.brakingPower = 1 / (0.036 * opts->brakingPower);
    state->attributes.size = opts->size;
}

void adjustState(State* state, unsigned elapsedMs) {
    state->distanceTaken = state->distanceTaken + state->speed * (elapsedMs / 1000.0);

    if (state->accelerationState == ACCELERATING) {
        state->speed = state->speed + state->attributes.acceleration * (elapsedMs / 1000.0);
        if (state->lane == EXPRESS_LANE && state->speed > state->attributes.maxSpeed) {
            state->speed = state->attributes.maxSpeed;
            state->accelerationState = MAINTAINING_SPEED;
        } else if (state->lane != EXPRESS_LANE && state->speed > state->attributes.preferredSpeed) {
            state->speed = state->attributes.preferredSpeed;
            state->accelerationState = MAINTAINING_SPEED;
        }
    } else if (state->accelerationState == BRAKING && state->speed > 0.0) {
        state->speed = state->speed - state->attributes.brakingPower * (elapsedMs / 1000.0);
        if (state->speed < 0.0) {
            state->speed = 0.0;
        }
    }

    // if we are changing lanes, increment the elapsed time
    switch (state->lane)
    {
    case MERGE_TO_TRAFFIC:
    case TRAFFIC_TO_EXPRESS:
    case EXPRESS_TO_TRAFFIC:
        state->laneChangeElapsed += elapsedMs;
        break;
    }

    // now if the counter is over the required time, we just zero it, and execute the lane change
    if (state->laneChangeElapsed > LANE_CHANGE_MS)
    {
        state->laneChangeElapsed = 0;
        switch (state->lane)
        {
        case MERGE_TO_TRAFFIC:
            state->lane = TRAFFIC_LANE;
            break;
        case TRAFFIC_TO_EXPRESS:
            state->lane = EXPRESS_LANE;
            break;
        case EXPRESS_TO_TRAFFIC:
            state->lane = TRAFFIC_LANE;
            break;
        }
    }
}

int attributesToString(Attributes* attributes, char* attributesStr) {
    return sprintf(attributesStr, "'preferred_speed':%f,'max_speed':%f,'acceleration':%f,'braking_power':%f,'size':%f",
            attributes->preferredSpeed, attributes->maxSpeed,
            attributes->acceleration, attributes->brakingPower, attributes->size);
}

int stateToString(State* state, char* stateStr) {
    return sprintf(stateStr, "'lane':%d,'distance_taken':%f,'speed':%f,'acceleration_state':%d",
            state->lane, state->distanceTaken, state->speed, state->accelerationState);
}
