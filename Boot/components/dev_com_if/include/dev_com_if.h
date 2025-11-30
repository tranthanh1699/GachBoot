#ifndef DEV_COM_IF_H
#define DEV_COM_IF_H
#include "dev_common.h"
#include "dev_com.h"


typedef dev_err_t (*dev_com_tp_receive_callback_t)(dev_mailbox_context_t *mailbox_ctx);

/**
 * @brief Initialize the communication interface.
 * @param receive_callback Pointer to the receive callback function.
 * @return Error code indicating success or failure.
 */
dev_err_t dev_com_if_init(dev_com_tp_receive_callback_t receive_callback);

/**
 * @brief Indicate reception of data over the communication interface.
 * @param data Pointer to the received data buffer
 * @param length Length of the received data
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure
 */
dev_err_t dev_com_if_rx_indication(dev_mailbox_context_t *mailbox_ctx);

/**
 * @brief Transmit data over the communication interface.
 * @param mailbox_ctx Pointer to the mailbox context containing data to send
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure
 */
dev_err_t dev_com_if_transmit(dev_mailbox_context_t * mailbox_ctx); 


#endif // DEV_COM_IF_H