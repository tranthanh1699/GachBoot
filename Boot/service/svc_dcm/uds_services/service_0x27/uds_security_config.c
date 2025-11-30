#include "uds_security_config.h"
#include "dcmdsl/dcmdsl.h"
#include <string.h>

CONFIG_LOG_TAG(SECURITY_CFG, true)

// Forward declarations of security callbacks
static Std_ReturnType security_get_seed_level_1(uint8_t security_level, uint8_t *seed);
static Std_ReturnType security_compare_key_level_1(uint8_t security_level, const uint8_t *key, const uint8_t *seed);
static Std_ReturnType security_get_seed_level_2(uint8_t security_level, uint8_t *seed);
static Std_ReturnType security_compare_key_level_2(uint8_t security_level, const uint8_t *key, const uint8_t *seed);

// Security Level Configuration (AUTOSAR DcmDspSecurityRow)
static const dcm_security_level_config_t security_level_config[] = {
    // Level  SubFunc_Seed  SubFunc_Key  SeedSize  KeySize  MaxAttempts  DelayTime  SessionMask                                       GetSeed                      CompareKey
    {1,       0x01,         0x02,        4,        4,       3,           10000,     UDS_SESSION_MASK_EXTENDED | UDS_SESSION_MASK_PROGRAMMING,  security_get_seed_level_1,   security_compare_key_level_1},
    {2,       0x03,         0x04,        8,        8,       3,           30000,     UDS_SESSION_MASK_PROGRAMMING,                              security_get_seed_level_2,   security_compare_key_level_2},
};

#define SECURITY_LEVEL_COUNT (sizeof(security_level_config) / sizeof(dcm_security_level_config_t))

// Security Level Runtime State
static dcm_security_level_state_t security_level_state[SECURITY_LEVEL_COUNT] = {0};

/**
 * @brief Find security level configuration
 */
const dcm_security_level_config_t* uds_security_find_config(uint8_t sub_function)
{
    for (uint16_t i = 0; i < SECURITY_LEVEL_COUNT; i++) {
        if (security_level_config[i].security_sub_function_seed == sub_function ||
            security_level_config[i].security_sub_function_key == sub_function) {
            return &security_level_config[i];
        }
    }
    return NULL;
}

/**
 * @brief Get security level state
 */
dcm_security_level_state_t* uds_security_get_state(uint8_t security_level)
{
    for (uint16_t i = 0; i < SECURITY_LEVEL_COUNT; i++) {
        if (security_level_config[i].security_level == security_level) {
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
    for (int16_t i = SECURITY_LEVEL_COUNT - 1; i >= 0; i--) {
        if (security_level_state[i].state == SECURITY_STATE_UNLOCKED) {
            return security_level_config[i].security_level;
        }
    }
    return 0;  // Locked
}

/**
 * @brief Reset all security levels
 */
void uds_security_reset_all(void)
{
    for (uint16_t i = 0; i < SECURITY_LEVEL_COUNT; i++) {
        security_level_state[i].state = SECURITY_STATE_LOCKED;
        security_level_state[i].failed_attempts = 0;
        security_level_state[i].lockout_start_time_ms = 0;
        memset(security_level_state[i].seed, 0, sizeof(security_level_state[i].seed));
    }
    DBG_OUT_I("All security levels reset");
}

/**
 * @brief Get system tick (application must implement)
 */
uint32_t uds_security_get_tick_ms(void)
{
    // TODO: Implement system tick retrieval (HAL_GetTick() for STM32)
    return DEV_GET_TICK_MS();
}

// ============================================================================
// Security Callback Implementations
// ============================================================================

/**
 * @brief Generate seed for Security Level 1
 */
static Std_ReturnType security_get_seed_level_1(uint8_t security_level, uint8_t *seed)
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
static Std_ReturnType security_compare_key_level_1(uint8_t security_level, const uint8_t *key, const uint8_t *seed)
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
static Std_ReturnType security_get_seed_level_2(uint8_t security_level, uint8_t *seed)
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
static Std_ReturnType security_compare_key_level_2(uint8_t security_level, const uint8_t *key, const uint8_t *seed)
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
