#include "uds_service_0x27.h"
#include "svc_dcm.h"
#include "dcmdsl/dcmdsl.h"
#include <string.h>

CONFIG_LOG_TAG(UDS_0x27, true)

#define UDS_SERVICE_SECURITY_TABLE security_level_config_table
#define UDS_SERVICE_SECURITY_TABLE_SIZE SECURITY_LEVEL_COUNT

// Security Level Runtime State
static dcm_security_level_state_t security_level_state[UDS_SERVICE_SECURITY_TABLE_SIZE] = {0};

/**
 * @brief Find security level configuration
 */
const dcm_security_level_config_t* uds_security_find_config(uint8_t sub_function)
{
    for (uint16_t i = 0; i < UDS_SERVICE_SECURITY_TABLE_SIZE; i++) {
        if (UDS_SERVICE_SECURITY_TABLE[i].security_sub_function_seed == sub_function ||
            UDS_SERVICE_SECURITY_TABLE[i].security_sub_function_key == sub_function) {
            return &UDS_SERVICE_SECURITY_TABLE[i];
        }
    }
    return NULL;
}

/**
 * @brief Get security level state
 */
dcm_security_level_state_t* uds_security_get_state(uint8_t security_level)
{
    for (uint16_t i = 0; i < UDS_SERVICE_SECURITY_TABLE_SIZE; i++) {
        if (UDS_SERVICE_SECURITY_TABLE[i].security_level == security_level) {
            return &security_level_state[i];
        }
    }
    return NULL;
}

/**
 * @brief Get current active security level
 */
uint8_t uds_security_get_active_level(void)
{
    // Return highest unlocked security level
    for (int16_t i = UDS_SERVICE_SECURITY_TABLE_SIZE - 1; i >= 0; i--) {
        if (security_level_state[i].state == SECURITY_STATE_UNLOCKED) {
            return UDS_SERVICE_SECURITY_TABLE[i].security_level;
        }
    }
    return 0;  // Locked
}

/**
 * @brief Get system tick (application must implement)
 */
uint32_t uds_security_get_tick_ms(void)
{
    return DEV_GET_TICK_MS();
}


/**
 * @brief Reset all security levels
 */
void uds_security_reset_all(void)
{
    for (uint16_t i = 0; i < UDS_SERVICE_SECURITY_TABLE_SIZE; i++) {
        security_level_state[i].state = SECURITY_STATE_LOCKED;
        security_level_state[i].failed_attempts = 0;
        security_level_state[i].lockout_start_time_ms = 0;
        memset(security_level_state[i].seed, 0, sizeof(security_level_state[i].seed));
    }
    DBG_OUT_I("All security levels reset");
}

/**
 * @brief Service 0x27 handler - Security Access
 */
Std_ReturnType uds_service_0x27_handler(const uds_message_t *message, ErrorCode_t *error_code)
{
    // Phase 1: Validate minimum request length (SID + Sub-function)
    if (message->request_len < 2) {
        DBG_OUT_E("Invalid message length: %d (minimum 2)", message->request_len);
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }

    uint8_t sub_function = message->request[1];
    
    DBG_OUT_I("Security Access: sub-function 0x%02X", sub_function);

    // Phase 2: Find security level configuration
    const dcm_security_level_config_t *config = uds_security_find_config(sub_function);
    if (config == NULL) {
        DBG_OUT_E("Sub-function 0x%02X not supported", sub_function);
        *error_code = UDS_NRC_SUBFUNCTION_NOT_SUPPORTED;
        return E_NOT_OK;
    }

    // Phase 3: Check session support
    uint8_t current_session = dcmdsl_get_session();
    uint32_t current_session_mask = 0;
    switch (current_session) {
        case UDS_SESSION_DEFAULT:
            current_session_mask = UDS_SESSION_MASK_DEFAULT;
            break;
        case UDS_SESSION_PROGRAMMING:
            current_session_mask = UDS_SESSION_MASK_PROGRAMMING;
            break;
        case UDS_SESSION_EXTENDED_DIAGNOSTIC:
            current_session_mask = UDS_SESSION_MASK_EXTENDED;
            break;
        default:
            current_session_mask = UDS_SESSION_MASK_DEFAULT;
            break;
    }

    if ((config->session_mask & current_session_mask) == 0) {
        DBG_OUT_E("Security level %d not allowed in session 0x%02X", 
                  config->security_level, current_session);
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }

    // Phase 4: Get security level state
    dcm_security_level_state_t *state = uds_security_get_state(config->security_level);
    if (state == NULL) {
        DBG_OUT_E("Security level %d state not found", config->security_level);
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }

    // Phase 5: Process request based on sub-function type
    bool is_request_seed = (sub_function == config->security_sub_function_seed);

    if (is_request_seed) {
        // ===== REQUEST SEED =====
        
        // Check if already unlocked
        if (state->state == SECURITY_STATE_UNLOCKED) {
            DBG_OUT_I("Security level %d already unlocked - sending zero seed", config->security_level);
            // Send zero seed (AUTOSAR: already unlocked) - data only, DCMDSP adds SID
            message->response[0] = sub_function;
            memset(&message->response[1], 0x00, config->seed_size);
            *(message->response_len) = 1 + config->seed_size;
            return E_OK;
        }

        // Check if in lockout period
        if (state->failed_attempts >= config->num_failed_security_access) {
            uint32_t current_time = uds_security_get_tick_ms();
            uint32_t elapsed_time = current_time - state->lockout_start_time_ms;
            
            if (elapsed_time < config->security_delay_time_ms) {
                DBG_OUT_E("Security level %d in lockout (remaining: %d ms)", 
                          config->security_level, config->security_delay_time_ms - elapsed_time);
                *error_code = UDS_NRC_REQUIRED_TIME_DELAY_NOT_EXPIRED;
                return E_NOT_OK;
            }
            
            // Lockout period expired - reset counter
            DBG_OUT_I("Lockout period expired, resetting counter");
            state->failed_attempts = 0;
        }

        // Validate request length (should be just SID + Sub-function for request seed)
        if (message->request_len != 2) {
            DBG_OUT_E("Invalid request seed length: %d (expected 2)", message->request_len);
            *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
            return E_NOT_OK;
        }

        // Generate seed
        Std_ReturnType seed_result = config->get_seed_callback(config->security_level, state->seed);
        if (seed_result != E_OK) {
            DBG_OUT_E("Failed to generate seed for level %d", config->security_level);
            *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
            return E_NOT_OK;
        }

        // Update state
        state->state = SECURITY_STATE_SEED_REQUESTED;

        // Build response
        message->response[0] = sub_function;
        memcpy(&message->response[1], state->seed, config->seed_size);
        *(message->response_len) = 1 + config->seed_size;

        DBG_OUT_I("Seed sent for security level %d", config->security_level);
        return E_OK;
    }
    else {
        // ===== SEND KEY =====
        
        // Check if already unlocked
        if (state->state == SECURITY_STATE_UNLOCKED) {
            DBG_OUT_I("Security level %d already unlocked", config->security_level);
            message->response[0] = sub_function;
            *(message->response_len) = 1;
            return E_OK;
        }

        // Check if seed was requested first
        if (state->state != SECURITY_STATE_SEED_REQUESTED) {
            DBG_OUT_E("Seed not requested for security level %d", config->security_level);
            *error_code = UDS_NRC_REQUEST_SEQUENCE_ERROR;
            return E_NOT_OK;
        }

        // Validate request length (SID + Sub-function + Key)
        if (message->request_len != (2 + config->key_size)) {
            DBG_OUT_E("Invalid key length: %d (expected %d)", 
                        message->request_len - 2, config->key_size);
            *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
            return E_NOT_OK;
        }

        // Extract key from request
        const uint8_t *received_key = &message->request[2];

        // Compare key
        Std_ReturnType key_result = config->compare_key_callback(config->security_level, 
                                                                received_key, 
                                                                state->seed);
        if (key_result == E_OK) {
            // Key valid - unlock security level
            state->state = SECURITY_STATE_UNLOCKED;
            state->failed_attempts = 0;
            
            DBG_OUT_I("Security level %d unlocked successfully", config->security_level);

            // Build positive response (data only, DCMDSP will add positive SID)
            message->response[0] = sub_function;
            *(message->response_len) = 1;
            return E_OK;
        }
        else {
            // Key invalid - increment failed attempts
            state->failed_attempts++;
            state->state = SECURITY_STATE_LOCKED;
            
            DBG_OUT_W("Invalid key for security level %d (attempt %d/%d)", 
                        config->security_level, state->failed_attempts, config->num_failed_security_access);

            // Check if max attempts exceeded
            if (state->failed_attempts >= config->num_failed_security_access) {
                state->lockout_start_time_ms = uds_security_get_tick_ms();
                DBG_OUT_E("Max attempts exceeded - entering lockout period (%d ms)", 
                            config->security_delay_time_ms);
                *error_code = UDS_NRC_EXCEED_NUMBER_OF_ATTEMPTS;
            } else {
                *error_code = UDS_NRC_INVALID_KEY;
            }
            
            return E_NOT_OK;
        }
    }
}

// ============================================================================
// Security Callback Implementations
// ============================================================================

/**
 * @brief Generate seed for Security Level 1
 */
Std_ReturnType security_get_seed_level_1(uint8_t security_level, uint8_t *seed)
{
    (void)security_level;
    
    // Simple seed generation (replace with crypto-grade RNG in production)
    uint32_t random_seed = uds_security_get_tick_ms() ^ 0xDEADBEEF;
    
    seed[0] = (random_seed >> 24) & 0xFF;
    seed[1] = (random_seed >> 16) & 0xFF;
    seed[2] = (random_seed >> 8) & 0xFF;
    seed[3] = random_seed & 0xFF;
    
    DBG_OUT_I("Level 1 seed generated: 0x%02X%02X%02X%02X", seed[0], seed[1], seed[2], seed[3]);
    return E_OK;
}

/**
 * @brief Compare key for Security Level 1
 */
Std_ReturnType security_compare_key_level_1(uint8_t security_level, const uint8_t *key, const uint8_t *seed)
{
    (void)security_level;
    
    // Simple key algorithm: key = seed XOR 0x12345678 (replace with proper crypto in production)
    uint32_t expected_key = ((uint32_t)seed[0] << 24) | ((uint32_t)seed[1] << 16) | 
                            ((uint32_t)seed[2] << 8) | seed[3];
    expected_key ^= 0x12345678;
    
    uint32_t received_key = ((uint32_t)key[0] << 24) | ((uint32_t)key[1] << 16) | 
                            ((uint32_t)key[2] << 8) | key[3];
    
    if (received_key == expected_key) {
        DBG_OUT_I("Level 1 key valid");
        return E_OK;
    }
    
    DBG_OUT_W("Level 1 key invalid (expected: 0x%08X, received: 0x%08X)", expected_key, received_key);
    return E_NOT_OK;
}

/**
 * @brief Generate seed for Security Level 2
 */
Std_ReturnType security_get_seed_level_2(uint8_t security_level, uint8_t *seed)
{
    (void)security_level;
    
    // More complex seed for level 2 (8 bytes)
    uint32_t tick = uds_security_get_tick_ms();
    uint32_t random1 = tick ^ 0xCAFEBABE;
    uint32_t random2 = (tick << 16) ^ 0xFEEDFACE;
    
    seed[0] = (random1 >> 24) & 0xFF;
    seed[1] = (random1 >> 16) & 0xFF;
    seed[2] = (random1 >> 8) & 0xFF;
    seed[3] = random1 & 0xFF;
    seed[4] = (random2 >> 24) & 0xFF;
    seed[5] = (random2 >> 16) & 0xFF;
    seed[6] = (random2 >> 8) & 0xFF;
    seed[7] = random2 & 0xFF;
    
    DBG_OUT_I("Level 2 seed generated: 0x%02X%02X%02X%02X%02X%02X%02X%02X", 
                seed[0], seed[1], seed[2], seed[3], seed[4], seed[5], seed[6], seed[7]);
    return E_OK;
}

/**
 * @brief Compare key for Security Level 2
 */
Std_ReturnType security_compare_key_level_2(uint8_t security_level, const uint8_t *key, const uint8_t *seed)
{
    (void)security_level;
    
    // More complex key algorithm for level 2 (replace with proper crypto in production)
    uint64_t seed_val = ((uint64_t)seed[0] << 56) | ((uint64_t)seed[1] << 48) |
                        ((uint64_t)seed[2] << 40) | ((uint64_t)seed[3] << 32) |
                        ((uint64_t)seed[4] << 24) | ((uint64_t)seed[5] << 16) |
                        ((uint64_t)seed[6] << 8) | seed[7];
    
    uint64_t expected_key = seed_val ^ 0x123456789ABCDEF0ULL;
    
    uint64_t received_key = ((uint64_t)key[0] << 56) | ((uint64_t)key[1] << 48) |
                            ((uint64_t)key[2] << 40) | ((uint64_t)key[3] << 32) |
                            ((uint64_t)key[4] << 24) | ((uint64_t)key[5] << 16) |
                            ((uint64_t)key[6] << 8) | key[7];
    
    if (received_key == expected_key) {
        DBG_OUT_I("Level 2 key valid");
        return E_OK;
    }
    
    DBG_OUT_W("Level 2 key invalid");
    return E_NOT_OK;
}