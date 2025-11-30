#ifndef SVC_APP_H
#define SVC_APP_H
#include "dev_common.h"
#include "dev_com.h"
#include "dev_com_if.h"
#include "dev_com_tp.h"

/* Service Application Initialization */
dev_err_t svc_app_init(void);

/**
 * @brief Service Application Main Run Loop
 */
void svc_app_run(void);

#endif // SVC_APP_H