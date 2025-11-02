#include "svc_app.h"

CONFIG_LOG_TAG(SVC_APP, true)
/* Service Application Initialization */
dev_err_t svc_app_init(void)
{
    dev_err_t err;

    DBG_OUT_I("Service Application Initialization Started");

    // Initialize UART Driver
    err = dev_uart_init();
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Failed to initialize UART Driver, Error: %d", err);

    // Initialize Communication Interface Layer
    err = dev_com_if_init(dev_com_tp_notification_callback);
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Failed to initialize Communication Interface Layer, Error: %d", err);

    // Initialize Transport Protocol Layer
    err = dev_com_tp_init();
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Failed to initialize Transport Protocol Layer, Error: %d", err);

    DBG_OUT_I("Service Application Initialization Completed Successfully");
    return DEV_OK;
}

/**
 * @brief Service Application Main Run Loop
 */
void svc_app_run(void)
{
    dev_com_if_main_function(); 
}