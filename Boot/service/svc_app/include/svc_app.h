#ifndef SVC_APP_H
#define SVC_APP_H
#include "dev_common.h"
#include "dev_com.h"
#include "dev_com_if.h"
#include "dev_com_tp.h"

/* Service Application Initialization */
void svc_app_init(void);

/* Periodic task (called every 1000ms) */
void svc_app_1000ms_task(void);

/* Background task (called from main loop) */
void svc_app_background_task(void);

#endif // SVC_APP_H