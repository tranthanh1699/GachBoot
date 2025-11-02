#ifndef DEV_COM_IF_H
#define DEV_COM_IF_H
#include "dev_common.h"
#include "dev_uart.h"

/* User define config */
#define DEV_COM_IF_CONFIG_BUFFER_SIZE   100  	// 100 bytes buffer size
#define DEV_COM_IF_CONFIG_MUTEX        	0    	// Enable mutex for thread safety
#define DEV_COM_IF_CONFIG_USE_RTOS    	0    	// Enable RTOS features

/* Library define */
#define DEV_COM_IF_SYNC0_FRAME       0x55
#define DEV_COM_IF_SYNC1_FRAME       0xAA
#define DEV_COM_IF_VERSION           0x01
#define DEV_COM_IF_TYPE              0x10
#define DEV_COM_IF_DLC_MAX           64
#define DEV_COM_IF_DLC_MIN           1

#define DEV_COM_IF_HEADER_SIZE      5   // Sync(2) + Version(1) + Type(1) + DLC(1)
#define DEV_COM_IF_FOOTER_SIZE      2   // CRC16(2)

#define DEV_COM_IF_SYNC0_INDEX    0
#define DEV_COM_IF_SYNC1_INDEX    1
#define DEV_COM_IF_VERSION_INDEX  2
#define DEV_COM_IF_TYPE_INDEX     3
#define DEV_COM_IF_DLC_INDEX      4
#define DEV_COM_IF_DATA_INDEX     5

typedef struct 
{
    uint8_t dlc; 
    uint8_t data[DEV_COM_IF_DLC_MAX];
} dev_com_if_packet_t;

/**
 * @brief Callback function type for receiving data, will be notify to upper layer.
 * @param data Pointer to the received data buffer.
 * @param length Length of the received data.
 */
typedef dev_err_t (*dev_com_if_receive_callback_t)(dev_com_if_packet_t * mailbox);

/**
 * @brief Initialize the communication interface.
 * @return Error code indicating success or failure.
 */
dev_err_t dev_com_if_init(dev_com_if_receive_callback_t receive_callback);

/**
 * @brief Main function to be called periodically or in RTOS task.
 * @return None
 */
#if DEV_COM_IF_CONFIG_USE_RTOS == 1
void dev_com_if_main_function(void * arg); 
#else
void dev_com_if_main_function(void);
#endif

/**
 * @brief Transmit data over the communication interface.
 * @param data Pointer to the data buffer to be sent
 * @param length Length of data to send
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure
 */
dev_err_t dev_com_if_transmit(const uint8_t *data, uint32_t length);


#endif // DEV_COM_IF_H