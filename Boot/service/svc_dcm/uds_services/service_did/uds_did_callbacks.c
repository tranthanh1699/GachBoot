/**
 * @file uds_did_callbacks.c
 * @brief DID Callback Function Implementations
 * 
 * This file implements all DID read/write/io_control callback functions.
 * These are the actual business logic for each DID operation.
 * 
 * @author GachBoot Team
 * @date 2024
 */

#include "uds_did_callbacks.h"
#include "dev_common.h"
#include "svc_dcm.h"
#include <string.h>

CONFIG_LOG_TAG(DID_CB, true)

/* ========================================================================== */
/*                    Read Callback Implementations                           */
/* ========================================================================== */

/**
 * @brief Read VIN (Vehicle Identification Number) - DID 0xF190
 * 
 * Returns 17-byte VIN string.
 * 
 * Example: Test pending response (simulates slow read operation)
 * - Returns DCM_E_PENDING for first 5 calls
 * - Returns E_OK with data on 6th call
 */
Std_ReturnType did_read_vin(uint8_t *data)
{
    // Return actual VIN data
    const uint8_t vin[] = "1HGBH41JXMN109186";  // 17 bytes
    memcpy(data, vin, 17);
    DBG_OUT_I("[DID 0xF190] VIN read: %.*s", 17, vin);
    return E_OK;
}

/**
 * @brief Read Boot Software ID - DID 0xF183
 * 
 * Returns 11-byte bootloader version string.
 */
Std_ReturnType did_read_boot_sw_id(uint8_t *data)
{
    const uint8_t boot_sw_id[] = "BOOT_V1.0.0";  // 11 bytes
    memcpy(data, boot_sw_id, 11);
    
    DBG_OUT_I("[DID 0xF183] Boot SW ID: %.*s", 11, boot_sw_id);
    return E_OK;
}

/**
 * @brief Read Application Software ID - DID 0xF184
 * 
 * Returns 10-byte application version string.
 */
Std_ReturnType did_read_app_sw_id(uint8_t *data)
{
    const uint8_t app_sw_id[] = "APP_V2.0.0";  // 10 bytes
    memcpy(data, app_sw_id, 10);
    
    DBG_OUT_I("[DID 0xF184] App SW ID: %.*s", 10, app_sw_id);
    return E_OK;
}

/**
 * @brief Read ECU Serial Number - DID 0xF18C
 * 
 * Returns 4-byte serial number in big-endian format.
 */
Std_ReturnType did_read_ecu_serial(uint8_t *data)
{
    // Example: 4-byte serial number
    uint32_t serial_number = 0x12345678;
    
    // Convert to big-endian
    data[0] = (serial_number >> 24) & 0xFF;
    data[1] = (serial_number >> 16) & 0xFF;
    data[2] = (serial_number >> 8) & 0xFF;
    data[3] = serial_number & 0xFF;
    
    DBG_OUT_I("[DID 0xF18C] ECU Serial: 0x%08X", serial_number);
    return E_OK;
}

/**
 * @brief Read ECU Configuration - DID 0xF100
 * 
 * Returns 2-byte configuration value.
 */
Std_ReturnType did_read_ecu_config(uint8_t *data)
{
    // Example: Read config from NVM or use default
    uint16_t config_value = 0x1234;
    
    data[0] = (config_value >> 8) & 0xFF;
    data[1] = config_value & 0xFF;
    
    DBG_OUT_I("[DID 0xF100] ECU Config: 0x%04X", config_value);
    return E_OK;
}

/* ========================================================================== */
/*                   Write Callback Implementations                           */
/* ========================================================================== */

/**
 * @brief Write Programming Fingerprint - DID 0xF15A
 * 
 * Stores programming fingerprint (variable length 1-32 bytes).
 * Typically used to track who programmed the ECU and when.
 * 
 * @note Length is pre-validated by registry (1-32 bytes)
 */
Std_ReturnType did_write_fingerprint(const uint8_t *data, uint16_t data_len)
{
    // TODO: Write to NVM (dev_nvm_write_block)
    
    DBG_OUT_I("[DID 0xF15A] Fingerprint written: %u bytes", data_len);
    
    // Log first few bytes for debugging
    if (data_len >= 3) {
        DBG_OUT_I("[DID 0xF15A] First bytes: 0x%02X 0x%02X 0x%02X...", 
            data[0], data[1], data[2]);
    }
    
    return E_OK;
}

/**
 * @brief Write Programming Date - DID 0xF199
 * 
 * Stores programming date (4 bytes: YYYY/MM/DD).
 * Performs semantic validation on date values.
 * 
 * Format:
 * - Byte 0-1: Year (big-endian, 2000-2099)
 * - Byte 2: Month (1-12)
 * - Byte 3: Day (1-31)
 * 
 * @note Length is pre-validated by registry (always 4 bytes)
 */
Std_ReturnType did_write_programming_date(const uint8_t *data, uint16_t data_len)
{
    (void)data_len;  // Always 4 bytes
    
    // Parse date components
    uint16_t year = (data[0] << 8) | data[1];
    uint8_t month = data[2];
    uint8_t day = data[3];
    
    // Semantic validation (application-level)
    if (year < 2000 || year > 2099) {
        DBG_OUT_E("[DID 0xF199] Invalid year: %u (must be 2000-2099)", year);
        return E_NOT_OK;
    }
    
    if (month < 1 || month > 12) {
        DBG_OUT_E("[DID 0xF199] Invalid month: %u (must be 1-12)", month);
        return E_NOT_OK;
    }
    
    if (day < 1 || day > 31) {
        DBG_OUT_E("[DID 0xF199] Invalid day: %u (must be 1-31)", day);
        return E_NOT_OK;
    }
    
    // TODO: Write to NVM (dev_nvm_write_block)
    
    DBG_OUT_I("[DID 0xF199] Programming date written: %04u/%02u/%02u", 
        year, month, day);
    
    return E_OK;
}

/**
 * @brief Write ECU Configuration - DID 0xF100
 * 
 * Stores ECU configuration value (2 bytes).
 * Performs semantic validation on config range.
 * 
 * @note Length is pre-validated by registry (always 2 bytes)
 */
Std_ReturnType did_write_ecu_config(const uint8_t *data, uint16_t data_len)
{
    (void)data_len;  // Always 2 bytes
    
    // Parse config value
    uint16_t config_value = (data[0] << 8) | data[1];
    
    // Semantic validation (example: max value 0x0FFF)
    if (config_value > 0x0FFF) {
        DBG_OUT_E("[DID 0xF100] Invalid config value: 0x%04X (max 0x0FFF)", 
            config_value);
        return E_NOT_OK;
    }
    
    // TODO: Write to NVM (dev_nvm_write_block)
    
    DBG_OUT_I("[DID 0xF100] ECU configuration written: 0x%04X", config_value);
    
    return E_OK;
}

/* ========================================================================== */
/*                IO Control Callback Implementations (Future)                */
/* ========================================================================== */

/* Add IO control callback implementations here when implementing Service 0x2F */
