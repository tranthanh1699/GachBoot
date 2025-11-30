#include "uds_rdbi_did_registry.h"
#include <string.h>

CONFIG_LOG_TAG(RDBI_DID, true)

// Forward declarations of DID read callbacks
static Std_ReturnType did_read_vin(uint8_t *data);
static Std_ReturnType did_read_boot_sw_id(uint8_t *data);
static Std_ReturnType did_read_app_sw_id(uint8_t *data);
static Std_ReturnType did_read_ecu_serial(uint8_t *data);

// DID Registry
static const uds_did_entry_t did_registry[] = {
    // DID      ExpLen  Callback                LengthGetter  Session Mask                                        Security Mask
    {0xF190,    17,     did_read_vin,           NULL,         UDS_SESSION_MASK_ALL,                              UDS_SECURITY_MASK_ALL},          // VIN - fixed 17 bytes
    {0xF183,    11,     did_read_boot_sw_id,    NULL,         UDS_SESSION_MASK_ALL,                              UDS_SECURITY_MASK_ALL},          // Boot SW ID - fixed 11 bytes
    {0xF184,    10,     did_read_app_sw_id,     NULL,         UDS_SESSION_MASK_ALL,                              UDS_SECURITY_MASK_ALL},          // App SW ID - fixed 10 bytes
    {0xF18C,    4,      did_read_ecu_serial,    NULL,         UDS_SESSION_MASK_DEFAULT | UDS_SESSION_MASK_EXTENDED,  UDS_SECURITY_MASK_ALL},      // ECU Serial - fixed 4 bytes
};

#define DID_REGISTRY_SIZE (sizeof(did_registry) / sizeof(uds_did_entry_t))

/**
 * @brief Find DID entry in registry
 */
const uds_did_entry_t* uds_rdbi_find_did(uint16_t did)
{
    for (uint16_t i = 0; i < DID_REGISTRY_SIZE; i++) {
        if (did_registry[i].did == did) {
            return &did_registry[i];
        }
    }
    return NULL;
}

/**
 * @brief Get DID registry
 */
const uds_did_entry_t* uds_rdbi_get_registry(uint16_t *count)
{
    *count = DID_REGISTRY_SIZE;
    return did_registry;
}

// ============================================================================
// DID Read Callback Implementations
// ============================================================================

/**
 * @brief Read VIN (Vehicle Identification Number)
 * Service handler guarantees buffer has 17 bytes available
 */
static Std_ReturnType did_read_vin(uint8_t *data)
{
    const uint8_t vin[] = "1HGBH41JXMN109186";
    memcpy(data, vin, 17);
    return E_OK;
}

/**
 * @brief Read Boot Software ID
 * Service handler guarantees buffer has 11 bytes available
 */
static Std_ReturnType did_read_boot_sw_id(uint8_t *data)
{
    const uint8_t boot_sw_id[] = "BOOT_V1.0.0";
    memcpy(data, boot_sw_id, 11);
    return E_OK;
}

/**
 * @brief Read Application Software ID
 * Service handler guarantees buffer has 10 bytes available
 */
static Std_ReturnType did_read_app_sw_id(uint8_t *data)
{
    const uint8_t app_sw_id[] = "APP_V2.0.0";
    memcpy(data, app_sw_id, 10);
    return E_OK;
}

/**
 * @brief Read ECU Serial Number
 * Service handler guarantees buffer has 4 bytes available
 */
static Std_ReturnType did_read_ecu_serial(uint8_t *data)
{
    // Example: 4-byte serial number
    uint32_t serial_number = 0x12345678;
    data[0] = (serial_number >> 24) & 0xFF;
    data[1] = (serial_number >> 16) & 0xFF;
    data[2] = (serial_number >> 8) & 0xFF;
    data[3] = serial_number & 0xFF;
    return E_OK;
}
