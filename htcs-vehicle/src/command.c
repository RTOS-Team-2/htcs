#include "command.h"
#include <stdio.h>

void keepPace();

void accelerate();

void brake();

void changeLane();

void processCommand(const Command cmd) {
    switch (cmd) {
        case KEEP_PACE:
            printf("Keep pace command received\n");
            keepPace();
            break;
        case ACCELERATE:
            printf("Accelerate command received\n");
            accelerate();
            break;
        case BRAKE:
            printf("Brake command received\n");
            brake();
            break;
        case CHANGE_LANE:
            printf("Change lane command received\n");
            changeLane();
            break;
        default:
            printf("Unknown command received\n");
    }
    fflush(stdout);
}

void keepPace() {
    // TODO
}

void accelerate() {
    // TODO
}

void brake() {
    // TODO
}

void changeLane() {
    // TODO
}
