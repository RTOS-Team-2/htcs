#ifndef HTCS_VEHICLE_SCHEDULER_H
#define HTCS_VEHICLE_SCHEDULER_H

typedef struct scheduler_sigdata {
    _Bool* keepRunning;
    void (*callback)();
} scheduler_sigdata;

void startRunning(_Bool* keepRunning, int intervalMs, void(*callback)());

#endif //HTCS_VEHICLE_SCHEDULER_H
