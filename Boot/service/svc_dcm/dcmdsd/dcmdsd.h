#ifndef DCMDSD_H
#define DCMDSD_H

#include "dev_common.h"
#include "dev_com_tp.h"

// Pending request configuration
#define DCMDSD_MAX_PENDING_NRC78_COUNT          15u     // Max NRC 0x78 transmissions before NRC 0x10
#define DCMDSD_PENDING_CALLBACK_RETRY_MS        10u     // Callback retry interval: 10ms (fast check)
#define DCMDSD_PENDING_NRC78_INTERVAL_MS        5000u   // NRC 0x78 transmission interval: 5 seconds

/**
 * @brief Pending request state
 */
typedef struct {
    bool is_pending;                        // Is there a pending request?
    uint8_t service_id;                     // Pending service ID
    uint8_t request_buffer[256];            // Stored request buffer
    uint16_t request_len;                   // Request length
    uint8_t target_address;                 // Target address for response
    uint16_t nrc78_count;                   // NRC 0x78 counter
    uint32_t last_nrc78_time_ms;            // Last NRC 0x78 transmission time
    uint32_t last_retry_time_ms;            // Last callback retry time
} dcmdsd_pending_state_t;

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

/**
 * @brief Process pending request (call periodically)
 */
void dcmdsd_process_pending(void);

/**
 * @brief Get system tick in milliseconds (must be implemented by application)
 */
uint32_t dcmdsd_get_tick_ms(void);

#endif // DCMDSD_H
