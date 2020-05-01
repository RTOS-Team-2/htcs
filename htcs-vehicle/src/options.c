#include "options.h"
#include <string.h>
#include <stdio.h>

void usage()
{
    printf("mqtt_gcloud\\\n");
    printf("\t--address <mqtt broker, e.g. maqiatto.com>\\\n");
    printf("\t--username <your username>\\\n");
    printf("\t--password <your password>\\\n");
    printf("\t--client_id <your client id>\\\n");
    fflush(stdout);
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
        } else if (strcmp(argv[pos], "--username") == 0) {
            if (++pos < argc) {
                opts->username = argv[pos];
            } else {
                return 3;
            }
        } else if (strcmp(argv[pos], "--password") == 0) {
            if (++pos < argc) {
                opts->password = argv[pos];
            } else {
                return 3;
            }
        } else if (strcmp(argv[pos], "--client_id") == 0) {
            if (++pos < argc) {
                opts->client_id = argv[pos];
            } else {
                return 3;
            }
        } else if (strcmp(argv[pos], "--topic") == 0) {
            if (++pos < argc) {
                opts->topic = argv[pos];
            } else {
                return 3;
            }
        }
        pos++;
    }
    return 0;
}