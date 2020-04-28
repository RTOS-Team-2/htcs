#ifndef MQTT_GCLOUD_MQTT_H
#define MQTT_GCLOUD_MQTT_H

#include <MQTTAsync.h>

MQTTAsync createAndConnect(const char* address, const char* username, const char* password,
                           const char* client_id, const int* keepRunning);

void onConnect(void* connected, MQTTAsync_successData* response);

void onConnectFailure(void* context, MQTTAsync_failureData* response);

void disconnect(void* context, MQTTAsync_failureData* response);

void onDisconnect(void* context, MQTTAsync_successData* response);

void onDisconnectFailure(void* context, MQTTAsync_failureData* response);

void connectionLost(void* context, char *cause);

int sendMessage(MQTTAsync client, char* topic, char* payload);

void onSend(void* context, MQTTAsync_successData* response);

int messageArrived(void* context, char* topicName, int topicLen, MQTTAsync_message* m);

#endif //MQTT_GCLOUD_MQTT_H
