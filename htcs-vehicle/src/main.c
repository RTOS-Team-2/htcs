#include <stdio.h>
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


#define TOPIC       "hello"
#define PAYLOAD     "Hello World!"

int keepRunning = 1;
int connected = 0;

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
		getchar();
        return 0;
    }

    MQTTAsync client = createClient(opts.address, opts.client_id);
    if (client == NULL)
    {
        return EXIT_FAILURE;
    }

    error = connectBroker(client, &connected);
    if (error)
    {
        return EXIT_FAILURE;
    }

    printf("Waiting for connection to %s\n", opts.address);
    while (!connected)
    {
        #if defined(_WIN32)
            Sleep(100);
        #else
            usleep(10000L);
        #endif
    }

    while (keepRunning)
    {
        error = sendMessage(client, TOPIC, PAYLOAD);
        if (error) break;
        #if defined(_WIN32)
            Sleep(1000);
        #else
            usleep(1000000L);
        #endif
    }

    disconnect(client, NULL);
    MQTTAsync_destroy(&client);
	getchar();
    return error;
}
