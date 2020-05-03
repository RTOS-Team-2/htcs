cmake_minimum_required(VERSION 3.7)
project(htcs_vehicle C)

set(CMAKE_C_STANDARD 99)
set(SOURCES
        src/main.c
        src/mqtt.c
        src/mqtt.h
        src/options.c
        src/options.h
        src/scheduler.c
        src/scheduler.h
        src/command.c
        src/command.h
        src/state.c src/state.h)
IF (WIN32)
    string(REPLACE "\\" "/" HOME $ENV{USERPROFILE})
    set(SUBMODULE_LIBS "${HOME}/eclipse-paho-mqtt-c-win32-1.3.1/lib")
    set(SUBMODULE_INCLUDES "${HOME}/eclipse-paho-mqtt-c-win32-1.3.1/include")
ELSE()
    set(SUBMODULE_LIBS "$ENV{HOME}/Eclipse-Paho-MQTT-C-1.3.1-Linux/lib")
    set(SUBMODULE_INCLUDES "$ENV{HOME}/Eclipse-Paho-MQTT-C-1.3.1-Linux/include")
ENDIF()


include_directories(${SUBMODULE_INCLUDES})
link_directories(${SUBMODULE_LIBS})

add_executable(htcs_vehicle ${SOURCES})

target_link_libraries(htcs_vehicle paho-mqtt3as rt)
