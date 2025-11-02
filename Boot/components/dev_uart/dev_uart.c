#include "dev_uart.h"
/* Device include lib */
#include "usart.h"
CONFIG_LOG_TAG(UART, true)

static dev_ringbuffer_t s_Uart_Ringbuffer;
volatile uint8_t rx_byte;
#if DEV_CONFIG_UART_MUTEX == 1
    #include "dev_mutex.h"
    dev_mutex_t s_Uart_Mutex;
#endif 
/**
 * @brief Write data to the ring buffer.
 * @param data Pointer to the data buffer to be sent (1 byte).
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
static dev_err_t dev_uart_set_buffer_uint8(uint8_t data); 

/**
 * @brief Set up UART receive interrupt.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure
 */
static dev_err_t dev_uart_set_rx_interrupt(void);

/* Device interrupt callback */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        dev_uart_set_buffer_uint8(rx_byte);
        dev_uart_set_rx_interrupt();
    }
}


/**
 * @brief Initialize the UART peripheral for communication.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_uart_init(void)
{
    dev_ringbuffer_init(&s_Uart_Ringbuffer, 1024); // Initialize ring buffer with 1KB size
#if DEV_CONFIG_UART_MUTEX == 1
    dev_mutex_init(&s_Uart_Mutex);
#endif
    dev_uart_set_rx_interrupt();
    return DEV_OK;
}

/**
 * @brief Deinitialize the UART peripheral.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_uart_deinit(void)
{
    dev_ringbuffer_deinit(&s_Uart_Ringbuffer);
#if DEV_CONFIG_UART_MUTEX == 1
    dev_mutex_deinit(&s_Uart_Mutex);
#endif
    return DEV_OK;
}

/**
 * @brief Get the number of available bytes in the UART ring buffer.
 * @return uint32_t Returns the number of bytes available to read.
 */
uint32_t dev_uart_available(void)
{
    uint32_t available_bytes = 0;

    #if DEV_CONFIG_UART_MUTEX == 1
        dev_mutex_lock(&s_Uart_Mutex);
    #endif

    available_bytes = dev_ringbuffer_size(&s_Uart_Ringbuffer);

    #if DEV_CONFIG_UART_MUTEX == 1
        dev_mutex_unlock(&s_Uart_Mutex);
    #endif

    return available_bytes;
}

/**
 * @brief Read data from the uart ring buffer.
 * @param data Pointer to the data buffer to be get (1 byte).
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_uart_get_uint8(uint8_t *data)
{
    dev_err_t err = DEV_OK;
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data pointer is NULL");

#if DEV_CONFIG_UART_MUTEX == 1
    dev_mutex_lock(&s_Uart_Mutex);
#endif
    uint32_t available_bytes = dev_ringbuffer_size(&s_Uart_Ringbuffer);
    if (available_bytes > 0)
    {
        dev_ringbuffer_read_uint8(&s_Uart_Ringbuffer, data);
    }
    else
    {
        // Handle case when no data is available
        err = DEV_ERR_NO_MEM;
    }

#if DEV_CONFIG_UART_MUTEX == 1
    dev_mutex_unlock(&s_Uart_Mutex);    
#endif
    return err;
}

/**
 * @brief Read data from the uart ring buffer.
 * @param data Pointer to the data buffer to be get
 * @param length Length of data to read
 * @param delimiter Delimiter byte to stop reading
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_uart_get_until(uint8_t *data, uint32_t length, uint8_t delimiter)
{
    dev_err_t err = DEV_OK;
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data pointer is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length must be greater than zero");

#if DEV_CONFIG_UART_MUTEX == 1
    dev_mutex_lock(&s_Uart_Mutex);
#endif
    uint32_t bytes_read = 0;
    while (bytes_read < length)
    {
        uint8_t byte;
        uint32_t available_bytes = dev_ringbuffer_size(&s_Uart_Ringbuffer);
        if (available_bytes > 0)
        {
            dev_ringbuffer_read_uint8(&s_Uart_Ringbuffer, &byte);
            if (byte == delimiter)
            {
                break; // Stop reading if delimiter is found
            }
            else
            {
                /* Store the byte in the data buffer */
                data[bytes_read++] = byte;
            }
        }
        else
        {
            // No more data available
            break;
        }
    }

#if DEV_CONFIG_UART_MUTEX == 1
    dev_mutex_unlock(&s_Uart_Mutex);        
#endif
    return err;
}

/**
 * @brief Transmit data over UART.
 * @param data Pointer to the data buffer to be sent
 * @param length Length of data to send
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_uart_transmit(const uint8_t *data, uint32_t length)
{
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data pointer is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length must be greater than zero");

    HAL_UART_Transmit(&huart1, (uint8_t *)data, length, 1000); // 1 second timeout
    return DEV_OK;
}

/**
 * @brief Write data to the ring buffer.
 * @param data Pointer to the data buffer to be sent (1 byte).
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
static dev_err_t dev_uart_set_buffer_uint8(uint8_t data)
{
    dev_err_t err = DEV_OK;
#if DEV_CONFIG_UART_MUTEX == 1
    dev_mutex_lock(&s_Uart_Mutex);
#endif

    if (dev_ringbuffer_free_space(&s_Uart_Ringbuffer) >= 1)
    {
        dev_ringbuffer_write_uint8(&s_Uart_Ringbuffer, data);
    }
    else
    {
        // Handle case when no space is available
        err = DEV_ERR_NO_MEM;
    }

#if DEV_CONFIG_UART_MUTEX == 1
    dev_mutex_unlock(&s_Uart_Mutex);
#endif
    return err;
}

static dev_err_t dev_uart_set_rx_interrupt(void)
{
    HAL_UART_Receive_IT(&huart1, (uint8_t *)&rx_byte, 1);
    return DEV_OK;
}