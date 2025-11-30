#ifndef DCMDSD_H
#define DCMDSD_H

#include "dev_common.h"
#include "dev_com_tp.h"

/**
 * @brief Initialize DSD layer
 */
dev_err_t dcmdsd_init(void);

/**
 * @brief Process diagnostic request - dispatch to appropriate service
 * @param sdu_info_p Pointer to SDU information
 * @return dev_err_t Error code
 */
dev_err_t dcmdsd_process_request(dev_com_tp_sdu_t * sdu_info_p);

/**
 * @brief Send positive response
 * @param sid Service ID
 * @param data Response data (after SID+0x40)
 * @param data_len Length of response data
 * @param address Target address
 */
void dcmdsd_send_positive_response(uint8_t sid, const uint8_t *data, uint16_t data_len, uint8_t address);

/**
 * @brief Send negative response
 * @param sid Service ID
 * @param nrc Negative Response Code
 * @param address Target address
 */
void dcmdsd_send_negative_response(uint8_t sid, uint8_t nrc, uint8_t address);

#endif // DCMDSD_H
