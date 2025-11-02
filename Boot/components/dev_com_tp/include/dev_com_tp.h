#ifndef DEV_COM_TP_H
#define DEV_COM_TP_H
#include "dev_com_if.h"


/**
 * @brief Initialize the transport protocol layer.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_tp_init(void);

/**
 * @brief Notification callback function for received data.
 * @param data Pointer to the received data buffer.
 * @param length Length of the received data.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_tp_notification_callback(const uint8_t *data, uint32_t length);

#endif // DEV_COM_TP_H