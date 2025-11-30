#include "dev_com_tp.h"
#include "include/dev_com_tp.h"

CONFIG_LOG_TAG(COM_TP, true)
static bool tp_initialized = false;
DEV_DELAY_CFG_NON_BLOCKING(tp_main_delay_timer);

// Static functions can be added here if needed
static dev_com_tp_rx_indication_cb_t rx_indication_callback = NULL;
/**
 * @brief Initialize the transport protocol layer.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_tp_init(dev_com_tp_rx_indication_cb_t rx_cb)
{
    // Initialization code for transport protocol layer
    DBG_OUT_I("Transport Protocol Layer Initialized");
    tp_initialized = true;
    rx_indication_callback = rx_cb;
#if DEV_CONFIG_COM_TP_USE_RTOS == 1
    // RTOS-specific initialization can be added here
    dev_rtos_create_task(dev_com_tp_main_function, "DevComTpTask", 1024, NULL, 1, NULL);
#endif // DEV_CONFIG_COM_TP_USE_RTOS == 1

    return DEV_OK;
}

/**
 * @brief Notification callback function for received data.
 * @param mailbox Pointer to the mailbox context containing received data.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_tp_rx_indication(dev_mailbox_context_t * mailbox)
{
    dev_err_t err; 
    DEV_RETURN_ON_FALSE(tp_initialized == true, DEV_ERR_MODULE_NOT_INIT, "Transport Protocol Layer not initialized");
    DEV_RETURN_ON_FALSE(mailbox != NULL, DEV_ERR_INVALID_ARG, "Mailbox pointer is NULL");
    DEV_RETURN_ON_FALSE(mailbox->mailbox_buffer != NULL, DEV_ERR_INVALID_ARG, "Mailbox buffer is NULL");
    DEV_RETURN_ON_FALSE(mailbox->mailbox_size > 0, DEV_ERR_INVALID_ARG, "Mailbox size must be greater than zero");
    
    // Direct passthrough - no frame processing
    dev_com_tp_sdu_t sdu_info;
    sdu_info.Address = mailbox->mailbox_id;
    sdu_info.SduBuffer = mailbox->mailbox_buffer;
    sdu_info.SduSize = mailbox->mailbox_size;
    
    // Call upper layer callback
    if (rx_indication_callback != NULL)
    {
        err = rx_indication_callback(&sdu_info);
        DEV_RETURN_ON_FALSE(err == DEV_OK, err, "RX Indication callback failed, Error: %d", err);
    }

    return DEV_OK;
}

/**
 * @brief Transmit data over the transport protocol layer.
 * @param mailbox Pointer to the mailbox context containing data to send.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_tp_transmit(dev_com_tp_sdu_t * sdu_info_p)
{
    dev_err_t err;
    DEV_RETURN_ON_FALSE(tp_initialized == true, DEV_ERR_MODULE_NOT_INIT, "Transport Protocol Layer not initialized");
    DEV_RETURN_ON_FALSE(sdu_info_p != NULL, DEV_ERR_INVALID_ARG, "SDU Info pointer is NULL");
    DEV_RETURN_ON_FALSE(sdu_info_p->SduBuffer != NULL, DEV_ERR_INVALID_ARG, "SDU Buffer pointer is NULL");
    DEV_RETURN_ON_FALSE(sdu_info_p->SduSize > 0, DEV_ERR_INVALID_ARG, "SDU Size must be greater than zero");

    // Direct passthrough - no frame wrapping
    dev_mailbox_context_t mailbox;
    mailbox.mailbox_id = sdu_info_p->Address;
    mailbox.mailbox_buffer = sdu_info_p->SduBuffer;
    mailbox.mailbox_size = sdu_info_p->SduSize;
    
    err = dev_com_if_transmit(&mailbox);
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Failed to transmit data via Communication Interface, Error: %d", err);
    return DEV_OK;
}

/**
 * @brief Main function for the transport protocol layer to be called periodically or in RTOS task.
 * @return None
 */
void dev_com_tp_main_function(void)
{
    // Main processing loop for transport protocol layer
#if DEV_CONFIG_COM_TP_USE_RTOS == 1
    while (1)
#else
    if (DEV_DELAY_NON_BLOCKING_MS(tp_main_delay_timer, 10)) // 10 ms interval
#endif
    {
        // Process incoming and outgoing packets here
        
#if DEV_CONFIG_COM_TP_USE_RTOS == 1
        // Yield to RTOS if applicable
        dev_rtos_yield();   
#endif
    }
}

/* =================== Static Function =================== */
// Frame processing removed - direct passthrough mode