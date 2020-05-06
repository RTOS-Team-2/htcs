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
#include "state.h"

#define INTERVAL_MS    250

static struct {
    MQTTAsync client;
    Options opts;
    _Bool keepRunning;
    State state;
    char topic[1024];
    char payload[1024];
} G_CTX;

void signalHandler(int signal);

void schedulerCallback();

void joinTraffic();

void exitTraffic();

int messageArrived(void* context, char* topicName, int topicLen, MQTTAsync_message* message);

int main(int argc, char* argv[]) {
	signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);

    int error = getOptions(&G_CTX.opts, argc, argv);
    if (error) {
        usage();
        #if defined(_WIN32)
        getchar();
        #endif
        return 0;
    }

    initializeState(&G_CTX.state, &G_CTX.opts);

    G_CTX.keepRunning = 1;

    G_CTX.client = createAndConnect(&G_CTX.opts, messageArrived, &G_CTX.keepRunning);
    if (G_CTX.client == NULL) {
        return EXIT_FAILURE;
    }
    subscribe(G_CTX.client, &G_CTX.opts, &G_CTX.keepRunning);

    joinTraffic();

    sprintf(G_CTX.topic, "%s/%s/state", G_CTX.opts.topic, G_CTX.opts.clientId);

    startRunning(&G_CTX.keepRunning, INTERVAL_MS, &schedulerCallback);

    exitTraffic();

    disconnect(G_CTX.client);
    #if defined(_WIN32)
    getchar();
    #endif
    return error;
}

void signalHandler(int signal) {
    G_CTX.keepRunning = 0;
}

void schedulerCallback() {
    adjustState(&G_CTX.state, INTERVAL_MS);
    int len = stateToString(&G_CTX.state, G_CTX.payload);
    int error = sendMessage(G_CTX.client, G_CTX.topic, G_CTX.payload, len, 0);
    if (error) {
        raise(SIGTERM);
    }
}

void joinTraffic() {
    sprintf(G_CTX.topic, "%s/%s/join", G_CTX.opts.topic, G_CTX.opts.clientId);
    int len = attributesToString(&G_CTX.state.attributes, G_CTX.payload);
    int error = sendMessage(G_CTX.client, G_CTX.topic, G_CTX.payload, len, 1);
    if (error) {
        fprintf(stderr, "Failed to join traffic, rc: %d\n", error);
        fflush(stderr);
        raise(SIGTERM);
    } else {
        printf("Joined traffic\n");
        fflush(stdout);
    }
}

void exitTraffic() {
    sprintf(G_CTX.topic, "%s/%s/join", G_CTX.opts.topic, G_CTX.opts.clientId);
    G_CTX.payload[0] = '\0'; // empty message
    int error = sendMessage(G_CTX.client, G_CTX.topic, G_CTX.payload, 1, 1);
    if (error) {
        fprintf(stderr, "Failed to exit traffic, rc: %d\n", error);
        fflush(stderr);
    } else {
        printf("Exited traffic\n");
        fflush(stdout);
    }
}

int messageArrived(void* context, char* topicName, int topicLen, MQTTAsync_message* message) {
    printf("Message arrived: %s\n", (char*)message->payload);
    fflush(stdout);

    Command cmd = ((char*)message->payload)[0] - '0';

    processCommand(cmd, &G_CTX.state);

    MQTTAsync_freeMessage(&message);
    MQTTAsync_free(topicName);
    return 1;
}
