#include "command.h"
#include <string.h>

Command parseCommand(const char* commandStr) {
    for (int i = 0; i < sizeof(CommandMapping) / sizeof(CommandMapping[0]); i++) {
        const char* str = CommandMapping[i].str;
        if (strncmp(str, commandStr, strlen(str)) == 0) {
            return CommandMapping[i].val;
        }
    }
    return UNKNOWN;
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
