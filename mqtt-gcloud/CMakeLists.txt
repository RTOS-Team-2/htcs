cmake_minimum_required(VERSION 3.16)
project(mqtt_gcloud C)

set(CMAKE_C_STANDARD 99)

include_directories(MQTT-C/include)

link_directories(MQTT-C/src)

add_executable(mqtt_gcloud main.c)
