#ifndef HTCS_VEHICLE_MQTT_H
#define HTCS_VEHICLE_MQTT_H

#include <MQTTAsync.h>
#include "options.h"

MQTTAsync createAndConnect(const Options* opts, void(*messageCallback)(const char*), const int* keepRunning);

void subscribe(MQTTAsync client, const Options* opts, const int* keepRunning);

void onConnect(void* connected, MQTTAsync_successData* response);

void onConnectFailure(void* context, MQTTAsync_failureData* response);

void disconnect(MQTTAsync client);

void onDisconnect(void* context, MQTTAsync_successData* response);

void onDisconnectFailure(void* context, MQTTAsync_failureData* response);

void connectionLost(void* context, char *cause);

int sendMessage(MQTTAsync client, char* topic, char* payload);

void onSend(void* context, MQTTAsync_successData* response);

int messageArrived(void* context, char* topicName, int topicLen, MQTTAsync_message* m);

void onSubscribe(void* context, MQTTAsync_successData* response);

void onSubscribeFailure(void* context, MQTTAsync_failureData* response);

#endif //HTCS_VEHICLE_MQTT_H
