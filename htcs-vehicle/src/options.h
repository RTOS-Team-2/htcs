#ifndef MQTT_GCLOUD_OPTIONS_H
#define MQTT_GCLOUD_OPTIONS_H

typedef struct
{
    char* address;
    char* username;
    char* password;
    char* client_id;
} options;

void usage();

int getOptions(options* opts, int argc, char** argv);

#endif //MQTT_GCLOUD_OPTIONS_H
