#ifndef HTCS_VEHICLE_MQTT_H
#define HTCS_VEHICLE_MQTT_H

#include <MQTTAsync.h>
#include "options.h"

#define QOS 1

MQTTAsync createAndConnect(const Options* opts, int(*messageArrived)(void*, char*, int, MQTTAsync_message*),
        const _Bool* keepRunning);

void subscribe(MQTTAsync client, const Options* opts, const _Bool* keepRunning);

void disconnect(MQTTAsync client);

int sendMessage(MQTTAsync client, char* topic, char* payload, int len);

#endif //HTCS_VEHICLE_MQTT_H
