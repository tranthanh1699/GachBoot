#include "dev_com_if.h"
#include "dev_uart.h"
#include "dev_crc.h"

CONFIG_LOG_TAG(COM_IF, true)

static dev_com_if_receive_callback_t s_Receive_Callback = NULL;

/* Data structure of interface packet
    Byte:    0      1      2     3     4         5..(5+DLC-1)    last-1  last
            +------+------+-----+-----+-----+---------------------+-------+------+
    Field   | SYNC0| SYNC1| VER |TYPE | DLC |         DATA        | (pad) |CRC16 |
            +------+------+-----+-----+-----+---------------------+-------+------+
    Size    |  1B  |  1B  | 1B  | 1B  | 1B  |   0..64 bytes       |  0B   |  2B  |
            +------+------+-----+-----+-----+---------------------+-------+------+
*/
/* Static function prototypes */
/**
 * @brief Process a received packet and validate it.
 * @param packet Pointer to the received packet buffer.
 * @param length Length of the received packet.
 * @return dev_err_t Returns DEV_OK if the packet is valid, or an appropriate error code on failure
 */
static dev_err_t dev_com_if_process_received_packet(const uint8_t *packet, uint32_t length);

/**
 * @brief Check the total length of the received packet.
 * @param packet Pointer to the received packet buffer. 
 * @param length Length of the received packet.
 * @return dev_err_t Returns DEV_OK if the length is valid, or DEV_ERR_INVALID_ARG on failure
 */
static dev_err_t dev_com_if_total_length_check(const uint8_t *packet, uint32_t length);

/**
 * @brief Check the sync bytes of the received packet.
 * @param packet Pointer to the received packet buffer. 
 * @return dev_err_t Returns DEV_OK if the sync bytes are valid, or DEV_ERR_INVALID_ARG on failure
 */
static dev_err_t dev_com_if_sync_check(const uint8_t *packet);

/**
 * @brief Check the CRC16 of the received packet.
 * @param packet Pointer to the received packet buffer.
 * @param length Length of the data, not including header and footer.
 * @return dev_err_t Returns DEV_OK if the CRC is valid, or DEV_ERR_INVALID_ARG on failure
 */
static dev_err_t dev_com_if_crc16_check(const uint8_t *packet, uint32_t length, uint16_t received_crc);

/**
 * @brief Create a mailbox structure from the received packet.
 * @param packet Pointer to the received packet buffer.
 * @param mailbox Pointer to the mailbox structure to be filled.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
static dev_err_t dev_com_if_create_mailbox(const uint8_t *packet, dev_com_if_packet_t *mailbox); 

/**
 * @brief Initialize the communication interface.
 * @return Error code indicating success or failure.
 */
dev_err_t dev_com_if_init(dev_com_if_receive_callback_t receive_callback)
{
    DEV_RETURN_ON_FALSE(receive_callback != NULL, DEV_ERR_INVALID_ARG, "Receive callback is NULL");

    // Store the receive callback
    s_Receive_Callback = receive_callback;
    
#if DEV_COM_IF_CONFIG_USE_RTOS == 1
    // RTOS-specific initialization can be added here
    dev_rtos_create_task(dev_com_if_main_function, "DevComIfTask", 1024, NULL, 1, NULL);
#endif // DEV_COM_IF_CONFIG_USE_RTOS == 1
    return DEV_OK;  
}

/**
 * @brief Main function to be called periodically or in RTOS task.
 * @return None
 */
#if DEV_COM_IF_CONFIG_USE_RTOS == 1
void dev_com_if_main_function(void * arg)
#else
void dev_com_if_main_function(void)
#endif 
{
#if DEV_COM_IF_CONFIG_USE_RTOS == 1
    while (1)
#endif
    {
        /* code */
        if(dev_uart_available() > 0)
        {
            uint8_t data[DEV_COM_IF_CONFIG_BUFFER_SIZE]; 
            dev_err_t err = dev_uart_get_until(data, DEV_COM_IF_CONFIG_BUFFER_SIZE, '\n');
            if (err == DEV_OK)
            {
                if (dev_com_if_process_received_packet(data, DEV_COM_IF_CONFIG_BUFFER_SIZE) == DEV_OK)
                {
                    // Call the receive callback with the received data
                    dev_com_if_packet_t mailbox;
                    if (dev_com_if_create_mailbox(data, &mailbox) == DEV_OK)
                    {
                        if (s_Receive_Callback != NULL)
                        {
                            s_Receive_Callback(&mailbox);
                        }
                    }
                }
            }
        }
#if DEV_COM_IF_CONFIG_USE_RTOS == 1
        dev_rtos_delay_ms(10); // Adjust delay as needed
#endif
    }
}

/**
 * @brief Transmit data over the communication interface.
 * @param data Pointer to the data buffer to be sent
 * @param length Length of data to send
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure
 */
dev_err_t dev_com_if_transmit(const uint8_t *data, uint32_t length)
{
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data pointer is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length must be greater than zero");

    return dev_uart_transmit(data, length);
}


/**
 * @brief Process a received packet and validate it.
 * @param packet Pointer to the received packet buffer.
 * @param length Length of the received packet.
 * @return dev_err_t Returns DEV_OK if the packet is valid, or an appropriate error code on failure
 */
static dev_err_t dev_com_if_process_received_packet(const uint8_t *packet, uint32_t length)
{
    dev_err_t err;
    DEV_RETURN_ON_FALSE(packet != NULL, DEV_ERR_INVALID_ARG, "Packet pointer is NULL");
    DEV_RETURN_ON_FALSE(length >= (DEV_COM_IF_HEADER_SIZE + DEV_COM_IF_DLC_MIN + DEV_COM_IF_FOOTER_SIZE), DEV_ERR_INVALID_ARG, "Length must be greater than 8");

    // Check sync bytes
    err = dev_com_if_sync_check(packet);
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Sync check failed");

    // Check total length
    err = dev_com_if_total_length_check(packet, length);
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Total length check failed");


    // check crc16
    uint16_t received_crc = (uint16_t)(packet[length - 2] << 8) | packet[length - 1];
    uint8_t dlc = packet[DEV_COM_IF_DLC_INDEX];
    err = dev_com_if_crc16_check(&packet[DEV_COM_IF_DATA_INDEX], dlc, received_crc);
    DEV_RETURN_ON_FALSE(err == DEV_OK, err, "CRC16 check failed");
    return DEV_OK;
}

/**
 * @brief Check the total length of the received packet.
 * @param packet Pointer to the received packet buffer. 
 * @param length Length of the received packet.
 * @return dev_err_t Returns DEV_OK if the length is valid, or DEV_ERR_INVALID_ARG on failure
 */
static dev_err_t dev_com_if_total_length_check(const uint8_t *packet, uint32_t length)
{
    DEV_RETURN_ON_FALSE(packet != NULL, DEV_ERR_INVALID_ARG, "Packet pointer is NULL");

    uint8_t dlc = packet[4]; // DLC is at byte index 4
    uint32_t expected_length = DEV_COM_IF_HEADER_SIZE + dlc + DEV_COM_IF_FOOTER_SIZE;

    DEV_RETURN_ON_FALSE(length == expected_length, DEV_ERR_INVALID_ARG, "Length mismatch: expected %d, got %d", expected_length, length);

    return DEV_OK;
}

/**
 * @brief Check the sync bytes of the received packet.
 * @param packet Pointer to the received packet buffer. 
 * @return dev_err_t Returns DEV_OK if the sync bytes are valid, or DEV_ERR_INVALID_ARG on failure
 */
static dev_err_t dev_com_if_sync_check(const uint8_t *packet)
{
    DEV_RETURN_ON_FALSE(packet[0] == DEV_COM_IF_SYNC0_FRAME, DEV_ERR_INVALID_ARG, "SYNC0 byte mismatch");
    DEV_RETURN_ON_FALSE(packet[1] == DEV_COM_IF_SYNC1_FRAME, DEV_ERR_INVALID_ARG, "SYNC1 byte mismatch");
    return DEV_OK;
}

/**
 * @brief Check the CRC16 of the received packet.
 * @param packet Pointer to the actual data, excluding header and footer.
 * @param length Length of the data, not including header and footer.
 * @return dev_err_t Returns DEV_OK if the CRC is valid, or DEV_ERR_INVALID_ARG on failure
 */
static dev_err_t dev_com_if_crc16_check(const uint8_t *packet, uint32_t length, uint16_t received_crc)
{
    DEV_RETURN_ON_FALSE(packet != NULL, DEV_ERR_INVALID_ARG, "Packet pointer is NULL");
    DEV_RETURN_ON_FALSE(length >= DEV_COM_IF_DLC_MIN, DEV_ERR_INVALID_ARG, "Length must be greater than 8");

    // Calculate CRC16 over the packet excluding the last 2 CRC bytes
    uint16_t calculated_crc = dev_crc16_calculate(packet, length);

    DEV_RETURN_ON_FALSE(received_crc == calculated_crc, DEV_ERR_CRC_FAIL, "CRC16 mismatch: expected 0x%04X, got 0x%04X", calculated_crc, received_crc);
    return DEV_OK;
}

/**
 * @brief Create a mailbox structure from the received packet.
 * @param packet Pointer to the received packet buffer.
 * @param mailbox Pointer to the mailbox structure to be filled.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
static dev_err_t dev_com_if_create_mailbox(const uint8_t *packet, dev_com_if_packet_t *mailbox)
{
    DEV_RETURN_ON_FALSE(packet != NULL, DEV_ERR_INVALID_ARG, "Packet pointer is NULL");
    DEV_RETURN_ON_FALSE(mailbox != NULL, DEV_ERR_INVALID_ARG, "Mailbox pointer is NULL");

    uint8_t dlc = packet[DEV_COM_IF_DLC_INDEX];
    DEV_RETURN_ON_FALSE(dlc <= DEV_COM_IF_DLC_MAX, DEV_ERR_INVALID_ARG, "DLC exceeds maximum limit");

    mailbox->dlc = dlc;
    for (uint8_t i = 0; i < dlc; i++)
    {
        mailbox->data[i] = packet[DEV_COM_IF_DATA_INDEX + i];
    }
    return DEV_OK;
}