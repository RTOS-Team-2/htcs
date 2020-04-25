#include <stdlib.h>
#include <stdio.h>

#include <mqtt.h>
#include "MQTT-C/examples/templates/openssl_sockets.h"

#define MQTT_HOST "mqtt.googleapis.com"
#define MQTT_PORT 8883
#define MQTT_CLIENT_ID "projects/team2-275116/locations/eu-west1/registries/team2-device-registry/devices/team2-test-device"

void publish_callback(void** unused, struct mqtt_response_publish *published);

int main() {
    printf("Hello, World!\n");

    uint8_t sendbuf[2048]; /* sendbuf should be large enough to hold multiple whole mqtt messages */
    uint8_t recvbuf[1024]; /* recvbuf should be large enough any whole mqtt message expected to be received */

    struct mqtt_client client;

    // TODO linuxon
    //mqtt_init(&client, sockfd, sendbuf, sizeof(sendbuf), recvbuf, sizeof(recvbuf), publish_callback);

    return 0;
}

void publish_callback(void** unused, struct mqtt_response_publish *published)
{
    /* not used in this example */
}