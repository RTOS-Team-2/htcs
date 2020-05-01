#ifndef HTCS_VEHICLE_COMMAND_H
#define HTCS_VEHICLE_COMMAND_H

typedef enum Commands {
    UNKNOWN,
    KEEP_PACE,
    ACCELERATE,
    BRAKE,
    CHANGE_LANE
} Command;

const static struct {
    Command val;
    const char* str;
} CommandMapping [] = {
        {KEEP_PACE,   "KEEP_PACE"},
        {ACCELERATE,  "ACCELERATE"},
        {BRAKE,       "BRAKE"},
        {CHANGE_LANE, "CHANGE_LANE"}
};

Command parseCommand(const char* commandStr);

void keepPace();

void accelerate();

void brake();

void changeLane();

#endif //HTCS_VEHICLE_COMMAND_H
