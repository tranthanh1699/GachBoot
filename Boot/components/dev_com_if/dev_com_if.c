#include "dev_com_if.h"
#include "dev_common.h"

CONFIG_LOG_TAG(COM_IF, true)
static bool s_Com_If_Initialized = false;
static dev_com_tp_receive_callback_t s_Receive_Callback = NULL;

/**
 * @brief Initialize the communication interface.
 * @return Error code indicating success or failure.
 */
dev_err_t dev_com_if_init(dev_com_tp_receive_callback_t receive_callback)
{
    DEV_RETURN_ON_FALSE(receive_callback != NULL, DEV_ERR_INVALID_ARG, "Receive callback is NULL");

    // Store the receive callback
    s_Receive_Callback = receive_callback;
#if DEV_COM_IF_CONFIG_USE_RTOS == 1
    // RTOS-specific initialization can be added here
    dev_rtos_create_task(dev_com_if_main_function, "DevComIfTask", 1024, NULL, 1, NULL);
#endif // DEV_COM_IF_CONFIG_USE_RTOS == 1
    s_Com_If_Initialized = true;
    return DEV_OK;  
}

/**
 * @brief Indicate reception of data over the communication interface.
 * @param data Pointer to the received data buffer
 * @param length Length of the received data
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure
 */
dev_err_t dev_com_if_rx_indication(dev_mailbox_context_t *mailbox_ctx)
{
    DEV_RETURN_ON_FALSE(s_Com_If_Initialized == true, DEV_ERR_INVALID_ARG, "Communication Interface not initialized");
    DEV_RETURN_ON_FALSE(mailbox_ctx != NULL, DEV_ERR_INVALID_ARG, "Mailbox context is NULL");
    DEV_RETURN_ON_FALSE(mailbox_ctx->mailbox_buffer != NULL, DEV_ERR_INVALID_ARG, "Mailbox buffer is NULL");
    DEV_RETURN_ON_FALSE(mailbox_ctx->mailbox_size > 0, DEV_ERR_INVALID_ARG, "Mailbox size must be greater than zero");

    // Call the registered receive callback
    if(s_Receive_Callback != NULL)
    {
        return s_Receive_Callback(mailbox_ctx);
    }
    return DEV_OK;   
}


/**
 * @brief Transmit data over the communication interface.
 * @param mailbox_ctx Pointer to the mailbox context containing data to send
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure
 */
dev_err_t dev_com_if_transmit(dev_mailbox_context_t * mailbox_ctx)
{
    DEV_RETURN_ON_FALSE(s_Com_If_Initialized == true, DEV_ERR_INVALID_ARG, "Communication Interface not initialized");
    DEV_RETURN_ON_FALSE(mailbox_ctx != NULL, DEV_ERR_INVALID_ARG, "Mailbox context is NULL");
    DEV_RETURN_ON_FALSE(mailbox_ctx->mailbox_buffer != NULL, DEV_ERR_INVALID_ARG, "Mailbox buffer is NULL");
    DEV_RETURN_ON_FALSE(mailbox_ctx->mailbox_size > 0, DEV_ERR_INVALID_ARG, "Mailbox size must be greater than zero");

    return dev_com_transmit(mailbox_ctx);
}
