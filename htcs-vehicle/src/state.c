#include "state.h"
#include <stdio.h>

#define DEFAULT_STARTING_SPEED 13.8888889

void initializeState(State *state, const Options *opts) {
    state->lane = opts->startingLane;
    state->distanceTaken = opts->startingDistance;
    state->speed = opts->startingSpeed == 0.0 ? DEFAULT_STARTING_SPEED : opts->startingSpeed / 3.6;
    state->laneChangeElapsed = 0;
    state->accelerationState = state->lane == TRAFFIC_LANE ? MAINTAINING_SPEED : ACCELERATING;

    state->attributes.preferredSpeed = opts->preferredSpeed / 3.6;
    state->attributes.maxSpeed = opts->maxSpeed / 3.6;
    state->attributes.acceleration = 1 / (0.036 * opts->acceleration);
    state->attributes.brakingPower = 1 / (0.036 * opts->brakingPower);
    state->attributes.size = opts->size;
}

void progressLaneChange(State *state, Lane lane, unsigned elapsedMs) {
    if (state->laneChangeElapsed >= LANE_CHANGE_MS) {
        state->laneChangeElapsed = 0;
        state->lane = lane;
    } else {
        state->laneChangeElapsed += elapsedMs;
    }
}

void adjustState(State *state, unsigned elapsedMs) {
    state->distanceTaken = state->distanceTaken + state->speed * (elapsedMs / 1000.0);

    if (state->accelerationState == ACCELERATING) {
        state->speed = state->speed + state->attributes.acceleration * (elapsedMs / 1000.0);
        if (state->lane == EXPRESS_LANE && state->speed > state->attributes.maxSpeed) {
            state->speed = state->attributes.maxSpeed;
            state->accelerationState = MAINTAINING_SPEED;
        } else if (state->lane != EXPRESS_LANE && state->speed > state->attributes.preferredSpeed) {
            state->accelerationState = MAINTAINING_SPEED;
        }
    } else if (state->accelerationState == BRAKING && state->speed > 0.0) {
        state->speed = state->speed - state->attributes.brakingPower * (elapsedMs / 1000.0);
        if (state->speed < 0.0) {
            state->speed = 0.0;
        }
    }

    switch (state->lane) {
        case MERGE_TO_TRAFFIC:
            progressLaneChange(state, TRAFFIC_LANE, elapsedMs);
            break;
        case TRAFFIC_TO_EXPRESS:
            progressLaneChange(state, EXPRESS_LANE, elapsedMs);
            break;
        case EXPRESS_TO_TRAFFIC:
            progressLaneChange(state, TRAFFIC_LANE, elapsedMs);
            break;
    }
}

int attributesAndStateToString(State *state, char *attributesStr) {
    return sprintf(attributesStr, "%.6f,%.6f,%.6f,%.6f,%.6f|%d,%.6f,%.6f,%d",
                   state->attributes.preferredSpeed, state->attributes.maxSpeed,
                   state->attributes.acceleration, state->attributes.brakingPower, state->attributes.size,
                   state->lane, state->distanceTaken, state->speed, state->accelerationState);
}

int stateToString(State *state, char *stateStr) {
    return sprintf(stateStr, "%d,%.6f,%.6f,%d",
                   state->lane, state->distanceTaken, state->speed, state->accelerationState);
}
