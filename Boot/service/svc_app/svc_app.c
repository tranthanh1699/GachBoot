#include "svc_app.h"
#include "stm32h7xx_hal_gpio.h"
#include "svc_dcm.h"

CONFIG_LOG_TAG(SVC_APP, true)
/* Service Application Initialization */
void svc_app_init(void)
{
    DBG_OUT_I("Service Application Initialization Started");
    // Initialize UART Driver
    (void)dev_com_init(dev_com_if_rx_indication);

    // Initialize Communication Interface Layer
    (void)dev_com_if_init(dev_com_tp_rx_indication);

    // Initialize Transport Protocol Layer
    (void)dev_com_tp_init(svc_notify_rx_indication);

    // Initialize DCM Service
    (void)svc_dcm_init();
}

void svc_app_1000ms_task(void)
{
    // This function is called every 1000 ms
    // Add periodic tasks here if needed
}