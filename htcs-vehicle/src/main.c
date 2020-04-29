#include <stdlib.h>
#include <signal.h>
#include "MQTTAsync.h"
#include "mqtt.h"
#include "options.h"
#if !defined(_WIN32)
#include <unistd.h>
#else
#include <windows.h>
#endif

#define PAYLOAD     "Hello World!"

int keepRunning = 1;

void signalHandler(int signal) {
    keepRunning = 0;
}

int main(int argc, char* argv[])
{
	#if defined(_WIN32)
	setvbuf(stdout, NULL, _IONBF, 0);
	#endif
	signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);

    options opts;
    int error = getOptions(&opts, argc, argv);
    if (error)
    {
        usage();
        #if defined(_WIN32)
        getchar();
        #endif
        return 0;
    }

    MQTTAsync client = createAndConnect(opts.address, opts.username, opts.password, opts.client_id, &keepRunning);
    if (client == NULL)
    {
        return EXIT_FAILURE;
    }

    while (keepRunning)
    {
        error = sendMessage(client, opts.topic, PAYLOAD);
        if (error) break;
        #if defined(_WIN32)
        Sleep(1000);
        #else
        usleep(1000000L);
        #endif
    }

    disconnect(client);
    #if defined(_WIN32)
    getchar();
    #endif
    return error;
}
