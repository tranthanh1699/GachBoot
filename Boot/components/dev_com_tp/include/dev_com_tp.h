#ifndef DEV_COM_TP_H
#define DEV_COM_TP_H
#include "dev_com_if.h"
#include "dev_com_tp_cfg.h"

#define DEV_CONFIG_COM_TP_USE_RTOS    DEV_CONFIG_COMMON_USE_RTOS

typedef struct 
{
    uint8_t Address;                // TP Address
    uint8_t FrameType;              // Frame Type
} dev_com_tp_rx_context_t;

typedef struct 
{
    uint8_t * PduBuffer;          // Pointer to PDU Buffer
    uint32_t PduSize;             // Size of the PDU Buffer
} dev_com_tp_pdu_t;

typedef struct 
{
    uint8_t Address;              // TP Address
    uint8_t * SduBuffer;          // Pointer to SDU Buffer
    uint16_t SduSize;             // Size of the SDU Buffer
} dev_com_tp_sdu_t;

typedef dev_err_t (* dev_com_tp_rx_indication_cb_t)(dev_com_tp_sdu_t * sdu_info_p);

/**
 * @brief Initialize the transport protocol layer.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_tp_init(dev_com_tp_rx_indication_cb_t rx_cb);

/**
 * @brief Notification callback function for received data.
 * @param mailbox Pointer to the mailbox context containing received data.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_tp_rx_indication(dev_mailbox_context_t * mailbox);

/**
 * @brief Transmit data over the transport protocol layer.
 * @param mailbox Pointer to the mailbox context containing data to send.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_com_tp_transmit(dev_com_tp_sdu_t * sdu_info_p); 

/**
 * @brief Main function for the transport protocol layer to be called periodically or in RTOS task.
 * @return None
 */
void dev_com_tp_main_function(void);

#endif // DEV_COM_TP_H