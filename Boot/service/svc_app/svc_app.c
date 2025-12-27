#include "svc_app.h"
#include "svc_dcm.h"

CONFIG_LOG_TAG(SVC_APP, true)
/* Service Application Initialization */
dev_err_t svc_app_init(void)
{
    dev_err_t err;

    DBG_OUT_I("Service Application Initialization Started");

    // Initialize UART Driver
    err = dev_com_init(dev_com_if_rx_indication);
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Failed to initialize UART Driver, Error: %d", err);

    // Initialize Communication Interface Layer
    err = dev_com_if_init(dev_com_tp_rx_indication);
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Failed to initialize Communication Interface Layer, Error: %d", err);

    // Initialize Transport Protocol Layer
    err = dev_com_tp_init(svc_notify_rx_indication);
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Failed to initialize Transport Protocol Layer, Error: %d", err);
    DBG_OUT_I("Service Application Initialization Completed Successfully");

    // Initialize DCM Service
    err = svc_dcm_init();
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Failed to initialize DCM Service, Error: %d", err);
    return DEV_OK;
}
