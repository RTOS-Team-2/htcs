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

#define PAYLOAD     "Hello World!"
#define INTERVAL_MS    1000

int keepRunning = 1;
MQTTAsync client;
options opts;

void signalHandler(int signal);

void schedulerCallback();

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

    client = createAndConnect(opts.address, opts.username, opts.password, opts.client_id, &keepRunning);
    if (client == NULL) {
        return EXIT_FAILURE;
    }

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
