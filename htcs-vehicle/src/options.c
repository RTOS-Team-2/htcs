#include "options.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

void usage() {
	printf("htcs_vehicle\\\n"
		"\t--address <mqtt broker, e.g. maqiatto.com>\\\n"
		"\t--username <mqtt username>\\\n"
		"\t--password <mqtt password>\\\n"
		"\t--clientId <arbitrary client id>\\\n"
		"\t--topic <topic base, e.g. krisz.kern@gmail.com/vehicles>\\\n"
		"\t--preferredSpeed <positive double in km/h, e.g. 120>\\\n"
		"\t--maxSpeed <positive double in km/h, e.g. 210>\\\n"
		"\t--acceleration <positive double, 0-100 km/h in seconds, e.g. 7.4>\\\n"
		"\t--brakingPower <positive double, 100-0 km/h in seconds, e.g. 9.2>\\\n"
		"\t--size <positive double in meters, e.g. 2.5>\\\n");
    fflush(stdout);
}

int getOptions(Options* opts, int argc, char** argv) {
    if (argc < 2) {
        return 1;
    }

    int pos = 1;
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
                return 4;
            }
        } else if (strcmp(argv[pos], "--clientId") == 0) {
            if (++pos < argc) {
                opts->clientId = argv[pos];
            } else {
                return 5;
            }
        } else if (strcmp(argv[pos], "--topic") == 0) {
            if (++pos < argc) {
                opts->topic = argv[pos];
            } else {
                return 6;
            }
        } else if (strcmp(argv[pos], "--preferredSpeed") == 0) {
            if (++pos < argc) {
                opts->preferredSpeed = strtod(argv[pos], NULL);
            } else {
                return 7;
            }
        } else if (strcmp(argv[pos], "--maxSpeed") == 0) {
            if (++pos < argc) {
                opts->maxSpeed = strtod(argv[pos], NULL);
            } else {
                return 8;
            }
        } else if (strcmp(argv[pos], "--acceleration") == 0) {
            if (++pos < argc) {
                opts->acceleration = strtod(argv[pos], NULL);
            } else {
                return 9;
            }
        } else if (strcmp(argv[pos], "--brakingPower") == 0) {
            if (++pos < argc) {
                opts->brakingPower = strtod(argv[pos], NULL);
            } else {
                return 10;
            }
        } else if (strcmp(argv[pos], "--size") == 0) {
            if (++pos < argc) {
                opts->size = strtod(argv[pos], NULL);
            } else {
                return 11;
            }
        }
        pos++;
    }

	if (opts->address == NULL || opts->username == NULL || opts->password == NULL ||
		opts->clientId == NULL || opts->topic == NULL || opts->preferredSpeed <= 0.0 ||
		opts->maxSpeed <= 0.0 || opts->acceleration <= 0.0 || opts->brakingPower <= 0.0 ||
		opts->size <= 0.0) {
		return 2;
	}

    return 0;
}