#include "mutex.h"

int mutex_init(MUTEX *mutex)
{
    #if defined(_WIN32)
    *mutex = CreateMutex(0, FALSE, 0);
    return (*mutex==0);
    #else
    return pthread_mutex_init(mutex, NULL);
    #endif
}

int mutex_lock(MUTEX *mutex)
{
    #if defined(_WIN32)
    return (WaitForSingleObject(*mutex, INFINITE)==WAIT_FAILED?1:0);
    #else
    return pthread_mutex_lock(mutex);
    #endif
}

int mutex_unlock(MUTEX *mutex) {
    #if defined(_WIN32)
    return (ReleaseMutex(*mutex)==0);
    #else
    return pthread_mutex_unlock(mutex);
    #endif
}