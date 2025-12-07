#ifndef UDS_SERVICE_0X27_H
#define UDS_SERVICE_0X27_H

#include "dev_common.h"
#include "dcmdsp/dcmdsp.h"
#include "Security_PBCfg.h"

// Security Access specific NRCs
#define UDS_NRC_INVALID_KEY                         0x35  // Invalid key
#define UDS_NRC_EXCEED_NUMBER_OF_ATTEMPTS           0x36  // Exceed number of attempts
#define UDS_NRC_REQUIRED_TIME_DELAY_NOT_EXPIRED     0x37  // Time delay not expired

/**
 * @brief Security level state
 */
typedef enum {
    SECURITY_STATE_LOCKED = 0,
    SECURITY_STATE_SEED_REQUESTED,
    SECURITY_STATE_UNLOCKED
} security_state_t;

/**
 * @brief Security level runtime state
 */
typedef struct {
    security_state_t state;                     // Current security state
    uint8_t seed[16];                           // Stored seed (max 16 bytes)
    uint8_t failed_attempts;                    // Failed attempt counter
    uint32_t lockout_start_time_ms;             // Lockout start timestamp
} dcm_security_level_state_t;

/**
 * @brief Find security level configuration
 * @param sub_function Sub-function ID (0x01, 0x02, 0x03, 0x04, ...)
 * @return Pointer to security level config, or NULL if not found
 */
const dcm_security_level_config_t* uds_security_find_config(uint8_t sub_function);

/**
 * @brief Get security level state
 * @param security_level Security level (1, 2, ...)
 * @return Pointer to security level state, or NULL if not found
 */
dcm_security_level_state_t* uds_security_get_state(uint8_t security_level);

/**
 * @brief Get current active security level
 * @return Current security level (0 = locked, 1 = level 1, 2 = level 2, ...)
 */
uint8_t uds_security_get_active_level(void);

/**
 * @brief Reset all security levels (e.g., on session change)
 */
void uds_security_reset_all(void);

/**
 * @brief Get system tick for timing (must be implemented by application)
 * @return Current system tick in milliseconds
 */
uint32_t uds_security_get_tick_ms(void);


/**
 * @brief Service 0x27 handler - Security Access
 * @param message Request and response message structure
 * @param error_code NRC if error (output)
 * @return Std_ReturnType E_OK (positive response), E_NOT_OK (negative response), DCM_E_PENDING (pending)
 */
Std_ReturnType uds_service_0x27_handler(const uds_message_t *message, ErrorCode_t *error_code);

#endif // UDS_SERVICE_0X27_H
