#include "mqtt.h"
#if !defined(_WIN32)
#include <unistd.h>
#else
#include <windows.h>
#endif
#include <string.h>
#include <signal.h>

void onConnect(void* connected, MQTTAsync_successData* response);

void onConnectFailure(void* context, MQTTAsync_failureData* response);

void onDisconnect(void* context, MQTTAsync_successData* response);

void onDisconnectFailure(void* context, MQTTAsync_failureData* response);

void connectionLost(void* context, char *cause);

void onSend(void* context, MQTTAsync_successData* response);

void onSubscribe(void* subscribed, MQTTAsync_successData* response);

void onSubscribeFailure(void* context, MQTTAsync_failureData* response);

MQTTAsync createAndConnect(const Options* opts, int(*messageArrived)(void*, char*, int, MQTTAsync_message*), const _Bool* keepRunning) {
    MQTTAsync client;
    int rc;
    if ((rc = MQTTAsync_create(&client, opts->address, opts->client_id,
            MQTTCLIENT_PERSISTENCE_NONE, NULL)) != MQTTASYNC_SUCCESS) {
        printf("Failed to create client object, return code %d\n", rc);
        fflush(stdout);
        return NULL;
    }

    if ((rc = MQTTAsync_setCallbacks(client, client, connectionLost, messageArrived, NULL)) != MQTTASYNC_SUCCESS) {
        printf("Failed to set callback, return code %d\n", rc);
        fflush(stdout);
        return NULL;
    }

    MQTTAsync_connectOptions conn_opts = MQTTAsync_connectOptions_initializer;
    conn_opts.keepAliveInterval = 20;
    conn_opts.cleansession = 1;
    conn_opts.username = opts->username;
    conn_opts.password = opts->password;
    conn_opts.onSuccess = onConnect;
    conn_opts.onFailure = onConnectFailure;
    _Bool connected = 0;
    conn_opts.context = &connected;
    if ((rc = MQTTAsync_connect(client, &conn_opts)) != MQTTASYNC_SUCCESS) {
        printf("Failed to start connect, return code %d\n", rc);
        fflush(stdout);
        return NULL;
    }

    printf("Waiting for connection to %s\n", opts->address);
    fflush(stdout);
    while (!connected && *keepRunning) {
        #if defined(_WIN32)
        Sleep(100);
        #else
        usleep(100000L);
        #endif
    }
    return client;
}

void subscribe(MQTTAsync client, const Options* opts, const _Bool* keepRunning) {
    // <topic_base>/<client_id>/command, e.g. krisz.kern@gmail.com/vehicles/1/command
    int subscribeTopicLen = (int)strlen(opts->topic) + 1 + (int)strlen(opts->client_id) + 1 + 7;
    char subscribeTopic[subscribeTopicLen];
    strcpy(subscribeTopic, opts->topic);
    strcat(subscribeTopic, "/");
    strcat(subscribeTopic, opts->client_id);
    strcat(subscribeTopic, "/command");

    printf("Subscribing to topic %s\n", subscribeTopic);
    fflush(stdout);

    MQTTAsync_responseOptions responseOptions = MQTTAsync_responseOptions_initializer;
    responseOptions.onSuccess = onSubscribe;
    responseOptions.onFailure = onSubscribeFailure;
    _Bool subscribed = 0;
    responseOptions.context = &subscribed;
    int rc;
    if ((rc = MQTTAsync_subscribe(client, subscribeTopic, 1, &responseOptions)) != MQTTASYNC_SUCCESS)
    {
        printf("Failed to start subscribe, return code %d\n", rc);
        fflush(stdout);
    }
    while (!subscribed && *keepRunning) {
        #if defined(_WIN32)
        Sleep(100);
        #else
        usleep(100000L);
        #endif
    }
}

int sendMessage(MQTTAsync client, char* topic, char* payload) {
    MQTTAsync_responseOptions opts = MQTTAsync_responseOptions_initializer;
    opts.onSuccess = onSend;
    opts.context = client;

    MQTTAsync_message message = MQTTAsync_message_initializer;
    message.payload = payload;
    message.payloadlen = (int)strlen(payload);
    message.qos = 1;
    message.retained = 0;
    int rc;
    if ((rc = MQTTAsync_sendMessage(client, topic, &message, &opts)) != MQTTASYNC_SUCCESS) {
        printf("Failed to start sendMessage, return code %d\n", rc);
        fflush(stdout);
    }
    return rc;
}

void disconnect(MQTTAsync client) {
    MQTTAsync_disconnectOptions opts = MQTTAsync_disconnectOptions_initializer;
    opts.onSuccess = onDisconnect;
    opts.onFailure = onDisconnectFailure;
    opts.context = client;
    int rc;
    if ((rc = MQTTAsync_disconnect(client, &opts)) != MQTTASYNC_SUCCESS) {
        printf("Failed to start disconnect, return code %d\n", rc);
        fflush(stdout);
    }
}

void onConnect(void* connected, MQTTAsync_successData* response) {
    printf("Successful connection\n");
    fflush(stdout);
    *((_Bool*)connected) = 1;
}

void onConnectFailure(void* context, MQTTAsync_failureData* response) {
    printf("Connect failed, rc: %d, message: %s\n",
            response ? response->code : 0, response ? response->message : "unknown");
    fflush(stdout);
    raise(SIGTERM);
}

void onDisconnect(void* context, MQTTAsync_successData* response) {
    printf("Successful disconnection\n");
    fflush(stdout);
    MQTTAsync client = (MQTTAsync) context;
    MQTTAsync_destroy(&client);
}

void onDisconnectFailure(void* context, MQTTAsync_failureData* response) {
    printf("Disconnect failed\n");
    fflush(stdout);
    MQTTAsync client = (MQTTAsync) context;
    MQTTAsync_destroy(&client);
}

void connectionLost(void *context, char *cause) {
    printf("\nConnection lost, cause: %s\n", cause);
    fflush(stdout);
    raise(SIGTERM);
}

void onSend(void* context, MQTTAsync_successData* response) {
    printf("Message with token value %d delivery confirmed\n", response->token);
    fflush(stdout);
}

void onSubscribe(void* subscribed, MQTTAsync_successData* response) {
    printf("Subscribe succeeded\n");
    fflush(stdout);
    *((_Bool*)subscribed) = 1;
}

void onSubscribeFailure(void* context, MQTTAsync_failureData* response) {
    printf("Subscribe failed, rc %d\n", response->code);
    fflush(stdout);
    raise(SIGTERM);
}
