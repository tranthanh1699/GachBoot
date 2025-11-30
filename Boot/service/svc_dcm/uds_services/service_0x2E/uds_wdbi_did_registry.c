#include "uds_wdbi_did_registry.h"
#include <string.h>

CONFIG_LOG_TAG(WDBI_DID, true)

// Forward declarations of DID write callbacks
static Std_ReturnType did_write_fingerprint(const uint8_t *data, uint16_t data_len);
static Std_ReturnType did_write_programming_date(const uint8_t *data, uint16_t data_len);
static Std_ReturnType did_write_ecu_config(const uint8_t *data, uint16_t data_len);

// DID Write Registry
static const uds_wdbi_did_entry_t wdbi_did_registry[] = {
    // DID      ExpLen  MinLen  MaxLen  Callback                        Session Mask                                            Security Mask
    {0xF15A,    0,      1,      32,     did_write_fingerprint,          UDS_SESSION_MASK_PROGRAMMING | UDS_SESSION_MASK_EXTENDED,  UDS_SECURITY_MASK_LEVEL_1 | UDS_SECURITY_MASK_LEVEL_2},  // Fingerprint - variable 1-32 bytes
    {0xF199,    4,      0,      0,      did_write_programming_date,     UDS_SESSION_MASK_PROGRAMMING,                              UDS_SECURITY_MASK_LEVEL_2},                              // Programming Date - fixed 4 bytes
    {0xF100,    2,      0,      0,      did_write_ecu_config,           UDS_SESSION_MASK_EXTENDED,                                 UDS_SECURITY_MASK_LEVEL_1 | UDS_SECURITY_MASK_LEVEL_2},  // ECU Config - fixed 2 bytes
};

#define WDBI_DID_REGISTRY_SIZE (sizeof(wdbi_did_registry) / sizeof(uds_wdbi_did_entry_t))

/**
 * @brief Find DID entry in write registry
 */
const uds_wdbi_did_entry_t* uds_wdbi_find_did(uint16_t did)
{
    for (uint16_t i = 0; i < WDBI_DID_REGISTRY_SIZE; i++) {
        if (wdbi_did_registry[i].did == did) {
            return &wdbi_did_registry[i];
        }
    }
    return NULL;
}

/**
 * @brief Get DID write registry
 */
const uds_wdbi_did_entry_t* uds_wdbi_get_registry(uint16_t *count)
{
    *count = WDBI_DID_REGISTRY_SIZE;
    return wdbi_did_registry;
}

// ============================================================================
// DID Write Callback Implementations
// ============================================================================

/**
 * @brief Write Fingerprint (variable length 1-32 bytes)
 * Service handler guarantees data_len is within 1-32 bytes
 */
static Std_ReturnType did_write_fingerprint(const uint8_t *data, uint16_t data_len)
{
    // TODO: Implement actual write to EEPROM/Flash
    DBG_OUT_I("Fingerprint written: %d bytes", data_len);
    DBG_OUT_I("First bytes: 0x%02X 0x%02X 0x%02X...", data[0], data[1], data[2]);
    return E_OK;
}

/**
 * @brief Write Programming Date (fixed 4 bytes: YYYY/MM/DD)
 * Service handler guarantees data_len is exactly 4 bytes
 */
static Std_ReturnType did_write_programming_date(const uint8_t *data, uint16_t data_len)
{
    (void)data_len;
    
    // Parse and validate date
    uint16_t year = (data[0] << 8) | data[1];
    uint8_t month = data[2];
    uint8_t day = data[3];
    
    // Semantic validation (application-level, not protocol-level)
    if (year < 2000 || year > 2099 || month < 1 || month > 12 || day < 1 || day > 31) {
        DBG_OUT_E("Invalid date: %04d/%02d/%02d", year, month, day);
        return E_NOT_OK;
    }
    
    // TODO: Implement actual write to EEPROM/Flash
    DBG_OUT_I("Programming date written: %04d/%02d/%02d", year, month, day);
    return E_OK;
}

/**
 * @brief Write ECU Configuration (fixed 2 bytes)
 * Service handler guarantees data_len is exactly 2 bytes
 */
static Std_ReturnType did_write_ecu_config(const uint8_t *data, uint16_t data_len)
{
    (void)data_len;
    
    uint16_t config_value = (data[0] << 8) | data[1];
    
    // Semantic validation (application-level)
    if (config_value > 0x0FFF) {
        DBG_OUT_E("Invalid ECU config value: 0x%04X (max 0x0FFF)", config_value);
        return E_NOT_OK;
    }
    
    // TODO: Implement actual write to EEPROM/Flash
    DBG_OUT_I("ECU configuration written: 0x%04X", config_value);
    return E_OK;
}
