#ifndef HTCS_VEHICLE_COMMAND_H
#define HTCS_VEHICLE_COMMAND_H

#include "state.h"

typedef enum Commands {
    MAINTAIN_SPEED,
    ACCELERATE,
    BRAKE,
    CHANGE_LANE
} Command;

void processCommand(Command cmd, State* state);

#endif //HTCS_VEHICLE_COMMAND_H
