#include "options.h"
#include <string.h>
#include <stdio.h>

void usage()
{
    printf("mqtt_gcloud\\\n");
    printf("\t--address <mqtt broker, e.g. tcp://35.242.192.152:1883>\\\n");
    printf("\t--client_id <your client id>\\\n");
}

int getOptions(options* opts, int argc, char** argv)
{
    int pos = 1;

    if (argc < 2) {
        return 1;
    }

    while (pos < argc) {
        if (strcmp(argv[pos], "--address") == 0) {
            if (++pos < argc) {
                opts->address = argv[pos];
            } else {
                return 2;
            }
        } else if (strcmp(argv[pos], "--client_id") == 0) {
            if (++pos < argc) {
                opts->client_id = argv[pos];
            } else {
                return 3;
            }
        }
        pos++;
    }
    return 0;
}