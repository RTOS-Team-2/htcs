#ifndef HTCS_VEHICLE_COMMAND_H
#define HTCS_VEHICLE_COMMAND_H

#include "state.h"
#include "mutex.h"

typedef enum Commands {
    MAINTAIN_SPEED,
    ACCELERATE,
    BRAKE,
    CHANGE_LANE,
    TERMINATE
} Command;

void processCommand(Command cmd, State* state, MUTEX* stateMutex);

#endif //HTCS_VEHICLE_COMMAND_H
