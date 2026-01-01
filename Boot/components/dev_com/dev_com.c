#include "dev_com.h"
/* Device include lib */
#include "dev_min.h"
#include "usbd_cdc_if.h"
CONFIG_LOG_TAG(COM, true)

#define MIN_PORT  0
#define MIN_TX_BUFFER_SIZE  512

static dev_ringbuffer_t s_Com_Ringbuffer;
static bool s_Com_Initialized = false;
static struct min_context s_Min_Context;
static dev_com_if_receive_callback_t s_Receive_Callback = NULL;
static uint8_t s_Min_Tx_Buffer[MIN_TX_BUFFER_SIZE];
static uint16_t s_Min_Tx_Index = 0;
volatile uint8_t rx_byte;
#if DEV_COM_CONFIG_MUTEX == 1
    #include "dev_mutex.h"
    dev_mutex_t s_Com_Mutex;
#endif

/* Complete dev_min Callback function */
void min_tx_start(uint8_t port) 
{
    // Reset buffer index when starting new frame
    s_Min_Tx_Index = 0;
    memset(s_Min_Tx_Buffer, 0, MIN_TX_BUFFER_SIZE);
}

void min_tx_finished(uint8_t port) 
{
    // Send entire buffered frame over USB
    if(s_Min_Tx_Index > 0) {
        CDC_Transmit_FS(s_Min_Tx_Buffer, s_Min_Tx_Index);
        s_Min_Tx_Index = 0;
    }
}

void min_tx_byte(uint8_t port, uint8_t byte) 
{
    // Buffer byte instead of sending immediately
    if(s_Min_Tx_Index < MIN_TX_BUFFER_SIZE) {
        s_Min_Tx_Buffer[s_Min_Tx_Index++] = byte;
    }
}

uint16_t min_tx_space(uint8_t port) {return MIN_TX_BUFFER_SIZE;}
uint32_t min_time_ms(void) {return DEV_GET_TICK_MS();}

void min_application_handler(uint8_t min_id, uint8_t const *min_payload, 
							uint8_t len_payload, uint8_t port)
{
    if (s_Receive_Callback != NULL)
    {
        dev_mailbox_context_t mailbox_ctx;
        mailbox_ctx.mailbox_id = min_id;
        mailbox_ctx.mailbox_buffer = (uint8_t *)min_payload;
        mailbox_ctx.mailbox_size = len_payload;
        s_Receive_Callback(&mailbox_ctx);
    }
    else 
    {
        // Do nothing if no callback registered
    }
}

/**
 * @brief Read data from the com ring buffer.
 * @param data Pointer to the data buffer to be get (1 byte).
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
static dev_err_t dev_com_get_uint8(uint8_t *data); 

/**
 * @brief Get the number of available bytes in the COM ring buffer.
 * @return uint32_t Returns the number of bytes available to read.
 */
static uint32_t dev_com_available(void); 

/**
 * @brief Initialize the COM peripheral for communication.
 * @param receive_callback Callback function to handle received data.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_init(dev_com_if_receive_callback_t receive_callback)
{
    DEV_RETURN_ON_FALSE(receive_callback != NULL, DEV_ERR_INVALID_ARG, "Receive callback is NULL");
    // Store the receive callback
    s_Receive_Callback = receive_callback;

    dev_ringbuffer_init(&s_Com_Ringbuffer, 1024); // Initialize ring buffer with 1KB size
#if DEV_COM_CONFIG_MUTEX == 1
    dev_mutex_init(&s_Com_Mutex);
#endif
    min_init_context(&s_Min_Context, MIN_PORT);
    s_Com_Initialized = true;
    return DEV_OK;
}

/**
 * @brief Deinitialize the COM peripheral.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_deinit(void)
{
    s_Com_Initialized = false;
    dev_ringbuffer_deinit(&s_Com_Ringbuffer);
#if DEV_COM_CONFIG_MUTEX == 1
    dev_mutex_deinit(&s_Com_Mutex);
#endif

#if DEV_COM_CONFIG_USE_RTOS == 1
    // RTOS-specific deinitialization can be added here 
    dev_rtos_create_task(dev_com_main_function, "DevComTask", 1024, NULL, 1, NULL);
#endif
    return DEV_OK;
}

/**
 * @brief Transmit data over COM.
 * @param mailbox_ctx Pointer to the mailbox context containing data to send.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_transmit(const dev_mailbox_context_t *mailbox_ctx)
{
    DEV_RETURN_ON_FALSE(s_Com_Initialized == true, 0, "COM not initialized");
    DEV_RETURN_ON_FALSE(mailbox_ctx != NULL, DEV_ERR_INVALID_ARG, "Mailbox context is NULL");
    DEV_RETURN_ON_FALSE(mailbox_ctx->mailbox_buffer != NULL, DEV_ERR_INVALID_ARG, "Mailbox buffer is NULL");
    DEV_RETURN_ON_FALSE(mailbox_ctx->mailbox_size > 0, DEV_ERR_INVALID_ARG, "Mailbox size must be greater than zero");
    min_send_frame(&s_Min_Context, mailbox_ctx->mailbox_id, mailbox_ctx->mailbox_buffer, mailbox_ctx->mailbox_size);
    return DEV_OK;
}


/**
 * @brief Main function to be called periodically or in RTOS task.
 * @return None
 */
void dev_com_main_function(void)
{
    if(dev_com_available() > 0)
    {
        uint8_t data;
        if (dev_com_get_uint8(&data) == DEV_OK)
        {
            min_poll(&s_Min_Context, &data, 1);
        }
    }
}

/**
 * @brief Get the number of available bytes in the COM ring buffer.
 * @return uint32_t Returns the number of bytes available to read.
 */
static uint32_t dev_com_available(void)
{
    DEV_RETURN_ON_FALSE(s_Com_Initialized == true, 0, "COM not initialized");
    uint32_t available_bytes = 0;

    #if DEV_COM_CONFIG_MUTEX == 1
        dev_mutex_lock(&s_Com_Mutex);
    #endif

    available_bytes = dev_ringbuffer_size(&s_Com_Ringbuffer);

    #if DEV_COM_CONFIG_MUTEX == 1
        dev_mutex_unlock(&s_Com_Mutex);
    #endif

    return available_bytes;
}

/**
 * @brief Read data from the com ring buffer.
 * @param data Pointer to the data buffer to be get (1 byte).
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
static dev_err_t dev_com_get_uint8(uint8_t *data)
{
    DEV_RETURN_ON_FALSE(s_Com_Initialized == true, 0, "COM not initialized");
    dev_err_t err = DEV_OK;
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data pointer is NULL");

#if DEV_COM_CONFIG_MUTEX == 1
    dev_mutex_lock(&s_Com_Mutex);
#endif
    uint32_t available_bytes = dev_ringbuffer_size(&s_Com_Ringbuffer);
    if (available_bytes > 0)
    {
        dev_ringbuffer_read_uint8(&s_Com_Ringbuffer, data);
    }
    else
    {
        // Handle case when no data is available
        err = DEV_ERR_NO_MEM;
    }

#if DEV_COM_CONFIG_MUTEX == 1
    dev_mutex_unlock(&s_Com_Mutex);    
#endif
    return err;
}


/**
 * @brief Write data to the ring buffer.
 * @param data Pointer to the data buffer to be sent (1 byte).
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_set_buffer_uint8(uint8_t data)
{
    dev_err_t err = DEV_OK;
    DEV_RETURN_ON_FALSE(s_Com_Initialized == true, 0, "COM not initialized");
#if DEV_COM_CONFIG_MUTEX == 1
    dev_mutex_lock(&s_Com_Mutex);
#endif

    if (dev_ringbuffer_free_space(&s_Com_Ringbuffer) >= 1)
    {
        dev_ringbuffer_write_uint8(&s_Com_Ringbuffer, data);
    }
    else
    {
        // Handle case when no space is available
        err = DEV_ERR_NO_MEM;
    }

#if DEV_COM_CONFIG_MUTEX == 1
    dev_mutex_unlock(&s_Com_Mutex);
#endif
    return err;
}
