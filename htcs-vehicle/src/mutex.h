#ifndef HTCS_VEHICLE_MUTEX_H
#define HTCS_VEHICLE_MUTEX_H

#if defined(_WIN32)
#include <windows.h>
#include <process.h>
#else
#include <pthread.h>
#endif

#if defined(_WIN32)
#define MUTEX HANDLE
#else
#define MUTEX pthread_mutex_t
#endif

int mutex_init(MUTEX *mutex);
int mutex_lock(MUTEX *mutex);
int mutex_unlock(MUTEX *mutex);

#endif //HTCS_VEHICLE_MUTEX_H
