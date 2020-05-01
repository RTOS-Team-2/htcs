#ifndef HTCS_VEHICLE_OPTIONS_H
#define HTCS_VEHICLE_OPTIONS_H

typedef struct
{
    char* address;
    char* username;
    char* password;
    char* client_id;
    char* topic;
} options;

void usage();

int getOptions(options* opts, int argc, char** argv);

#endif //HTCS_VEHICLE_OPTIONS_H
