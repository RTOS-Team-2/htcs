cmake_minimum_required(VERSION 3.7)
project(mqtt_gcloud C)

set(CMAKE_C_STANDARD 99)
set(SOURCES main.c mqtt.c mqtt.h options.c options.h)
set(SUBMODULE_LIBS "$ENV{HOME}/.local/lib")
set(SUBMODULE_INCLUDES "$ENV{HOME}/.local/include")

include_directories(${SUBMODULE_INCLUDES})
link_directories(${SUBMODULE_LIBS})

add_executable(mqtt_gcloud ${SOURCES})

target_link_libraries(mqtt_gcloud paho-mqtt3a)
