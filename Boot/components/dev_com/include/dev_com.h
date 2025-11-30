#ifndef DEV_COM_H
#define DEV_COM_H
#include "dev_common.h"
#include "dev_ringbuffer.h"

#define DEV_COM_CONFIG_MUTEX 		 	0     // Enable mutex for thread safety
#define DEV_COM_CONFIG_USE_RTOS    	    0    	// Enable RTOS features

typedef struct
{
    uint8_t mailbox_id;               // Mailbox identifier
    uint8_t *mailbox_buffer;          // Pointer to mailbox data buffer
    uint32_t mailbox_size;            // Size of the mailbox buffer
} dev_mailbox_context_t;

typedef dev_err_t (*dev_com_if_receive_callback_t)(dev_mailbox_context_t *mailbox_ctx);

/**
 * @brief Initialize the COM peripheral for communication.
 * @param receive_callback Callback function to handle received data.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_init(dev_com_if_receive_callback_t receive_callback);

/**
 * @brief Deinitialize the COM peripheral.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_deinit(void);

/**
 * @brief Transmit data over COM.
 * @param mailbox_ctx Pointer to the mailbox context containing data to send.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_transmit(const dev_mailbox_context_t *mailbox_ctx);

/**
 * @brief Main function to be called periodically or in RTOS task.
 * @return None
 */
void dev_com_main_function(void);

#endif // DEV_COM_H