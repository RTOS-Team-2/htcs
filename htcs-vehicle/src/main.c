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

static struct {
    MQTTAsync client;
    Options opts;
    _Bool keepRunning;
} G_HTCSV_Context;

void signalHandler(int signal);

void schedulerCallback();

int messageArrived(void* context, char* topicName, int topicLen, MQTTAsync_message* message);

int main(int argc, char* argv[]) {
	signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);

    int error = getOptions(&G_HTCSV_Context.opts, argc, argv);
    if (error) {
        usage();
        #if defined(_WIN32)
        getchar();
        #endif
        return 0;
    }

    G_HTCSV_Context.keepRunning = 1;

    G_HTCSV_Context.client = createAndConnect(&G_HTCSV_Context.opts, messageArrived, &G_HTCSV_Context.keepRunning);
    if (G_HTCSV_Context.client == NULL) {
        return EXIT_FAILURE;
    }
    subscribe(G_HTCSV_Context.client, &G_HTCSV_Context.opts, &G_HTCSV_Context.keepRunning);

    startRunning(&G_HTCSV_Context.keepRunning, INTERVAL_MS, &schedulerCallback);

    disconnect(G_HTCSV_Context.client);
    #if defined(_WIN32)
    getchar();
    #endif
    return error;
}

void signalHandler(int signal) {
    G_HTCSV_Context.keepRunning = 0;
}

void schedulerCallback() {
    int error = sendMessage(G_HTCSV_Context.client, G_HTCSV_Context.opts.topic, PAYLOAD);
    if (error)
    {
        raise(SIGTERM);
    }
}

int messageArrived(void* context, char* topicName, int topicLen, MQTTAsync_message* message) {
    printf("Message arrived: %s\n", (char*)message->payload);
    fflush(stdout);

    Command cmd = ((char*)message->payload)[0] - '0';

    processCommand(cmd);

    MQTTAsync_freeMessage(&message);
    MQTTAsync_free(topicName);
    return 1;
}
