#ifndef UDS_SECURITY_CONFIG_H
#define UDS_SECURITY_CONFIG_H

#include "dev_common.h"
#include "svc_dcm.h"

// Security Access Sub-functions (ISO 14229-1)
#define UDS_SA_REQUEST_SEED_LEVEL_1         0x01    // Request seed for level 1
#define UDS_SA_SEND_KEY_LEVEL_1             0x02    // Send key for level 1
#define UDS_SA_REQUEST_SEED_LEVEL_2         0x03    // Request seed for level 2
#define UDS_SA_SEND_KEY_LEVEL_2             0x04    // Send key for level 2

// Security Access specific NRCs
#define UDS_NRC_INVALID_KEY                 0x35    // Invalid key
#define UDS_NRC_EXCEED_NUMBER_OF_ATTEMPTS   0x36    // Exceed number of attempts
#define UDS_NRC_REQUIRED_TIME_DELAY_NOT_EXPIRED  0x37  // Time delay not expired

/**
 * @brief Security level state
 */
typedef enum {
    SECURITY_STATE_LOCKED = 0,
    SECURITY_STATE_SEED_REQUESTED,
    SECURITY_STATE_UNLOCKED
} security_state_t;

/**
 * @brief Seed generation callback
 * Generate a seed for security access
 * @param security_level Security level (1, 2, ...)
 * @param seed Output seed buffer (guaranteed to have DCM_SECURITY_SEED_SIZE bytes)
 * @return Std_ReturnType E_OK, E_NOT_OK
 */
typedef Std_ReturnType (*uds_security_get_seed_t)(uint8_t security_level, uint8_t *seed);

/**
 * @brief Key comparison callback
 * Compare received key with expected key
 * @param security_level Security level (1, 2, ...)
 * @param key Received key buffer
 * @param seed Previously sent seed buffer
 * @return Std_ReturnType E_OK (key valid), E_NOT_OK (key invalid)
 */
typedef Std_ReturnType (*uds_security_compare_key_t)(uint8_t security_level, const uint8_t *key, const uint8_t *seed);

/**
 * @brief Security level configuration entry (AUTOSAR-like)
 */
typedef struct {
    uint8_t security_level;                     // Security level (1, 2, ...)
    uint8_t security_sub_function_seed;         // Sub-function for request seed (0x01, 0x03, ...)
    uint8_t security_sub_function_key;          // Sub-function for send key (0x02, 0x04, ...)
    uint8_t seed_size;                          // Seed size in bytes
    uint8_t key_size;                           // Key size in bytes
    uint8_t num_failed_security_access;         // Max failed attempts before lockout
    uint32_t security_delay_time_ms;            // Delay time after failed attempts (ms)
    uint32_t session_mask;                      // Allowed sessions for security access
    uds_security_get_seed_t get_seed_callback;  // Seed generation callback
    uds_security_compare_key_t compare_key_callback;  // Key comparison callback
} dcm_security_level_config_t;

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

#endif // UDS_SECURITY_CONFIG_H
