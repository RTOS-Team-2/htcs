#ifndef HTCS_VEHICLE_COMMAND_H
#define HTCS_VEHICLE_COMMAND_H

typedef enum Commands {
    KEEP_PACE,
    ACCELERATE,
    BRAKE,
    CHANGE_LANE
} Command;

void processCommand(Command cmd);

#endif //HTCS_VEHICLE_COMMAND_H
