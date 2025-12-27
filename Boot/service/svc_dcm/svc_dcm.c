#include "svc_dcm.h"
#include "dcmdsl/dcmdsl.h"
#include "dcmdsd/dcmdsd.h"
#include "dcmdsp/dcmdsp.h"
#include "uds_services/service_0x11/uds_service_0x11.h"

CONFIG_LOG_TAG(DCM_SVC, true)
static bool dcm_initialized = false;
DEV_DELAY_CFG_NON_BLOCKING(dcm_main_delay_timer);

/**
 * @brief Initialize the DCM service
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t svc_dcm_init(void)
{
    dev_err_t err;
    
    // Initialize all DCM layers
    err = dcmdsl_init();
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Failed to initialize DCMDSL");
    
    err = dcmdsd_init();
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Failed to initialize DCMDSD");
    
    err = dcmdsp_init();
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Failed to initialize DCMDSP");
    
    DBG_OUT_I("DCM Service Initialized");
    dcm_initialized = true;
    return DEV_OK;
}

void svc_dcm_main_function(void)
{
    // DSL manages timing and session
    dcmdsl_main_function(SVC_DCM_TICK_INTERVAL_MS);
    
    // DSD processes pending requests
    dcmdsd_process_pending();
    
    // Process pending ECU reset
    uds_service_0x11_process_reset();
}

/**
 * @brief Notify DCM service of received SDU
 * @param sdu_info_p Pointer to the received SDU information
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t svc_notify_rx_indication(dev_com_tp_sdu_t * sdu_info_p)
{
    DEV_RETURN_ON_FALSE(dcm_initialized == true, DEV_ERR_MODULE_NOT_INIT, "DCM Service not initialized");
    DEV_RETURN_ON_FALSE(sdu_info_p != NULL, DEV_ERR_INVALID_ARG, "SDU Info pointer is NULL");
    DEV_RETURN_ON_FALSE(sdu_info_p->SduBuffer != NULL, DEV_ERR_INVALID_ARG, "SDU Buffer is NULL");
    DEV_RETURN_ON_FALSE(sdu_info_p->SduSize > 0, DEV_ERR_INVALID_ARG, "SDU Size must be greater than zero");
    
    // Forward to DSL for processing
    return dcmdsl_process_request(sdu_info_p);
}
