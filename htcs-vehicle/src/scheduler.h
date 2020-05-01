#ifndef HTCS_VEHICLE_SCHEDULER_H
#define HTCS_VEHICLE_SCHEDULER_H

typedef struct scheduler_sigdata {
    int* keepRunning;
    void (*callback)();
} scheduler_sigdata;

void startRunning(int* keepRunning, int intervalMs, void(*callback)());

#endif //HTCS_VEHICLE_SCHEDULER_H
