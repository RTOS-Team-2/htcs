#include "scheduler.h"


#if defined(_WIN32)
// Windows Implementation
#include <windows.h>

void startRunning(const int* keepRunning, int intervalSeconds, void(*callback)())
{
    while (*keepRunning)
    {
        callback();
        Sleep(intervalSeconds * 1000);
    }
}

#else
// Linux RT implementation
// TODO



#endif
