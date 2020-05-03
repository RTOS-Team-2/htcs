#ifndef HTCS_VEHICLE_OPTIONS_H
#define HTCS_VEHICLE_OPTIONS_H

typedef struct Options {
    char* address;
    char* username;
    char* password;
    char* clientId;
    char* topic;
    double preferredSpeed;
    double maxSpeed;
    double acceleration;
    double brakingPower;
    double size;
} Options;

void usage();

int getOptions(Options* opts, int argc, char** argv);

#endif //HTCS_VEHICLE_OPTIONS_H
