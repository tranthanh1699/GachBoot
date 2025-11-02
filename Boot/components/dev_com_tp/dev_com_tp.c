#include "dev_com_tp.h"

CONFIG_LOG_TAG(COM_TP, true)
static bool tp_initialized = false;
/**
 * @brief Initialize the transport protocol layer.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_tp_init(void)
{
    // Initialization code for transport protocol layer
    DBG_OUT_I("Transport Protocol Layer Initialized");
    tp_initialized = true;
    return DEV_OK;
}

/**
 * @brief Notification callback function for received data.
 * @param data Pointer to the received data buffer.
 * @param length Length of the received data.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_tp_notification_callback(dev_com_if_packet_t * mailbox)
{
    DEV_RETURN_ON_FALSE(tp_initialized == true, DEV_ERR_MODULE_NOT_INIT, "Transport Protocol Layer not initialized");
    DEV_RETURN_ON_FALSE(mailbox != NULL, DEV_ERR_INVALID_ARG, "Mailbox pointer is NULL");
    // Process the received packet
    DBG_OUT_I("Received packet with DLC: %d", mailbox->dlc);
    DBG_OUT_HEX(mailbox->data, mailbox->dlc);
    return DEV_OK;
}