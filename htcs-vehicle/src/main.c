#include <stdlib.h>
#include <signal.h>
#if !defined(_WIN32)
#include <unistd.h>
#else
#include <windows.h>
#endif
#include "MQTTAsync.h"
#include "mqtt.h"
#include "options.h"
#include "scheduler.h"
#include "command.h"

#define PAYLOAD     "Hello World!"
#define INTERVAL_MS    1000

int keepRunning = 1;
MQTTAsync client;
Options opts;

void signalHandler(int signal);

void schedulerCallback();

void processCommand(const char* command);

int main(int argc, char* argv[]) {
	signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);

    int error = getOptions(&opts, argc, argv);
    if (error) {
        usage();
        #if defined(_WIN32)
        getchar();
        #endif
        return 0;
    }

    client = createAndConnect(&opts, processCommand, &keepRunning);
    if (client == NULL) {
        return EXIT_FAILURE;
    }
    subscribe(client, &opts, &keepRunning);

    startRunning(&keepRunning, INTERVAL_MS, &schedulerCallback);

    disconnect(client);
    #if defined(_WIN32)
    getchar();
    #endif
    return error;
}

void signalHandler(int signal) {
    keepRunning = 0;
}

void schedulerCallback() {
    int error = sendMessage(client, opts.topic, PAYLOAD);
    if (error)
    {
        keepRunning = 0;
    }
}

void processCommand(const char* commandStr) {
    Command comm = parseCommand(commandStr);
    switch (comm) {
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
            printf("Unknown command received: %s\n", commandStr);
    }
    fflush(stdout);
}
