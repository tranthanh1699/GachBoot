#ifndef DEV_UART_H
#define DEV_UART_H
#include "dev_common.h"
#include "dev_ringbuffer.h"

#define DEV_CONFIG_UART_BUFFER_SIZE    	1024  // 1KB buffer size
#define DEV_CONFIG_UART_MUTEX 		 	0     // Enable mutex for thread safety

/**
 * @brief Initialize the UART peripheral for communication.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_uart_init(void);

/**
 * @brief Deinitialize the UART peripheral.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_uart_deinit(void);

/**
 * @brief Get the number of available bytes in the UART ring buffer.
 * @return uint32_t Returns the number of bytes available to read.
 */
uint32_t dev_uart_available(void);

/**
 * @brief Write data to the UART peripheral.
 * @param data Pointer to the data buffer to be get (1 byte).
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_uart_get_uint8(uint8_t *data);

/**
 * @brief Read data from the uart ring buffer.
 * @param data Pointer to the data buffer to be get
 * @param length Length of data to read
 * @param delimiter Delimiter byte to stop reading
 * @return uint32_t Returns the number of bytes read
 */
uint32_t dev_uart_get_until(uint8_t *data, uint32_t length, uint8_t delimiter); 

/**
 * @brief Transmit data over UART.
 * @param data Pointer to the data buffer to be sent
 * @param length Length of data to send
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_uart_transmit(const uint8_t *data, uint32_t length);
#endif // DEV_UART_H