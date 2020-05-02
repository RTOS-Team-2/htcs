#ifndef HTCS_VEHICLE_OPTIONS_H
#define HTCS_VEHICLE_OPTIONS_H

typedef struct Options {
    char* address;
    char* username;
    char* password;
    char* client_id;
    char* topic;
} Options;

void usage();

int getOptions(Options* opts, int argc, char** argv);

#endif //HTCS_VEHICLE_OPTIONS_H
