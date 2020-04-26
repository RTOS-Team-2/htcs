#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "MQTTClient.h"
#include "openssl/evp.h"
#include "iot_mqtt_jwt.h"

struct {
    char* address;
    char client_id[256];
    char* device_id;
    char* key_path;
    char* project_id;
    char* region;
    char* registry_id;
    char* root_path;
    char topic[256];
    char* payload;
    char* algorithm;
} opts = {.address = "ssl://mqtt.googleapis.com:8883",
        .client_id =
        "projects/team2-275116/locations/europe-west1/"
        "registries/team2-device-registry/devices/team2-test-device",
        .device_id = "team2-test-device",
        .key_path = "/home/kkern/elte/ARI/2019-2020-2/RTOS/rsa_private.pem",
        .project_id = "team2-275116",
        .region = "europe-west1",
        .registry_id = "team2-device-registry",
        .root_path = "/home/kkern/elte/ARI/2019-2020-2/RTOS/roots.pem",
        .topic = "projects/team2-275116/topics/test-topic",
        .payload = "Hello world!",
        .algorithm = "RS256"};

int main() {
    char* payload = "Hello, World!";

    int rc = - 1;
    MQTTClient client = {0};
    MQTTClient_connectOptions conn_opts = MQTTClient_connectOptions_initializer;

    MQTTClient_create(&client, opts.address, opts.client_id,
                      MQTTCLIENT_PERSISTENCE_NONE, NULL);
    conn_opts.keepAliveInterval = 60;
    conn_opts.cleansession = 1;
    conn_opts.username = "unused";
    conn_opts.password = CreateJwt(opts.key_path, opts.project_id, opts.algorithm);
    MQTTClient_SSLOptions sslopts = MQTTClient_SSLOptions_initializer;

    sslopts.trustStore = opts.root_path;
    sslopts.privateKey = opts.key_path;
    conn_opts.ssl = &sslopts;

    unsigned long retry_interval_ms = 500L;
    unsigned long total_retry_time_ms = 0;
    while ((rc = MQTTClient_connect(client, &conn_opts)) != MQTTCLIENT_SUCCESS) {
        if (rc == 3) {  // connection refused: server unavailable
            usleep(retry_interval_ms * 1000);
            total_retry_time_ms += retry_interval_ms;
            if (total_retry_time_ms >= 900000L) {
                printf("Failed to connect, maximum retry time exceeded.");
                exit(EXIT_FAILURE);
            }
            retry_interval_ms *= 1.5f;
            if (retry_interval_ms > 6000L) {
                retry_interval_ms = 6000L;
            }
        } else {
            printf("Failed to connect, return code %d\n", rc);
            exit(EXIT_FAILURE);
        }
    }

    MQTTClient_message pubmsg = MQTTClient_message_initializer;
    MQTTClient_deliveryToken token = {0};

    pubmsg.payload = payload;
    pubmsg.payloadlen = strlen(payload);
    pubmsg.qos = 1;
    pubmsg.retained = 0;
    MQTTClient_publishMessage(client, opts.topic, &pubmsg, &token);
    printf(
            "Waiting for up to %lu seconds for publication of %s\n"
            "on topic %s for client with ClientID: %s\n",
            (10000L / 1000), opts.payload, opts.topic, opts.client_id);
    rc = MQTTClient_waitForCompletion(client, token, 10000L);
    printf("Message with delivery token %d delivered\n", token);

    MQTTClient_disconnect(client, 10000);
    MQTTClient_destroy(&client);

    EVP_cleanup();
    return 0;
}
