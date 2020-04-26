#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include "MQTTAsync.h"
#include "mqtt.h"
#include "options.h"

#define TOPIC       "hello"
#define PAYLOAD     "Hello World!"

int keepRunning = 1;
int connected = 0;

void signalHandler(int signal) {
    keepRunning = 0;
}

int main(int argc, char* argv[])
{
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);

    options opts;
    int error = getOptions(&opts, argc, argv);
    if (error)
    {
        usage();
        return 0;
    }

    MQTTAsync client = createClient(opts.address, opts.client_id);
    if (client == NULL)
    {
        return EXIT_FAILURE;
    }

    error = connectBroker(client, &connected);
    if (error)
    {
        return EXIT_FAILURE;
    }

    printf("Waiting for connection to %s\n", opts.address);
    while (!connected)
    {
        usleep(10000L);
    }

    while (keepRunning)
    {
        error = sendMessage(client, TOPIC, PAYLOAD);
        if (error) break;
        usleep(1000000L);
    }

    disconnect(client, NULL);
    MQTTAsync_destroy(&client);
    return error;
}
