/**
 * @file uds_did_registry.c
 * @brief Unified DID Registry Implementation
 * 
 * This file contains the centralized DID configuration table and
 * implementation functions for DID registry access.
 * 
 * @author GachBoot Team
 * @date 2024
 */

#include "uds_did_registry.h"
#include "dev_common.h"
#include "svc_dcm.h"
#include <string.h>
#include "DID_PBCfg.h"  // Generated DID registry

#define DID_REGISTRY_GENERATED uds_did_registry_generated
#define DID_REGISTRY_COUNT (sizeof(DID_REGISTRY_GENERATED) / sizeof(uds_did_entry_t))

CONFIG_LOG_TAG(DID_REG, true)

const uint8_t rom_default_vin[17];
uint8_t ram_mirror_vin[17];
/* ========================================================================== */
/*                         Registry Access Functions                          */
/* ========================================================================== */

/**
 * @brief Find DID entry in registry
 */
const uds_did_entry_t* uds_did_registry_find(uint16_t did)
{
    for (uint16_t i = 0; i < DID_REGISTRY_COUNT; i++) {
        if (DID_REGISTRY_GENERATED[i].did == did) {
            return &DID_REGISTRY_GENERATED[i];
        }
    }
    
    DBG_OUT_W("[DID Registry] DID 0x%04X not found", did);
    return NULL;
}

/**
 * @brief Validate DID access for service in current session/security
 * @note Updated signature to use mask parameters instead of raw values
 */
Std_ReturnType uds_did_validate_access(
    uint16_t did,
    uint8_t service,
    uint32_t session_mask,
    uint32_t security_mask
)
{
    const uds_did_entry_t *entry = uds_did_registry_find(did);
    if (entry == NULL) {
        return E_NOT_OK;
    }
    
    uint32_t required_session_mask = 0;
    uint32_t required_security_mask = 0;
    
    // Get required masks for service
    switch (service) {
        case UDS_SID_READ_DATA_BY_IDENTIFIER:
            if (entry->read_config.callback == NULL) {
                return E_NOT_OK;    // Service not supported
            }
            required_session_mask = entry->read_config.session_mask;
            required_security_mask = entry->read_config.security_mask;
            break;
            
        case UDS_SID_WRITE_DATA_BY_IDENTIFIER:
            if (entry->write_config.callback == NULL) {
                return E_NOT_OK;
            }
            required_session_mask = entry->write_config.session_mask;
            required_security_mask = entry->write_config.security_mask;
            break;
            
        case UDS_SID_IO_CONTROL_BY_IDENTIFIER:
            break;
            
        default:
            return E_NOT_OK;
    }
    
    // Validate session - check if current session_mask matches required
    if ((session_mask & required_session_mask) == 0) {
        DBG_OUT_W("[DID Registry] DID 0x%04X service 0x%02X: Session mismatch", did, service);
        return E_NOT_OK;
    }
    
    // Validate security - check if current security_mask matches required
    // If required_security_mask is 0, no security is required
    if (required_security_mask != 0) {
        if ((security_mask & required_security_mask) == 0) {
            DBG_OUT_W("[DID Registry] DID 0x%04X service 0x%02X: Security access denied", did, service);
            return E_NOT_OK;
        }
    }
    
    return E_OK;
}


/**
 * @brief Validate DID data length
 */
bool uds_did_validate_length(uint16_t did, uint8_t service, uint16_t length)
{
    const uds_did_entry_t *entry = uds_did_registry_find(did);
    if (entry == NULL) {
        return false;
    }
    
    // Fixed length DID
    if (entry->expected_length > 0) {
        if (length != entry->expected_length) {
            DBG_OUT_W("[DID Registry] DID 0x%04X: Length mismatch (expected %u, got %u)",
                did, entry->expected_length, length);
            return false;
        }
        return true;
    }
    
    // Variable length DID
    if (length < entry->min_length || length > entry->max_length) {
        DBG_OUT_W("[DID Registry] DID 0x%04X: Length out of range (min %u, max %u, got %u)",
            did, entry->min_length, entry->max_length, length);
        return false;
    }
    
    return true;
}

Std_ReturnType uds_did_read_vin(uint8_t *data)
{
    return E_OK; 
}

Std_ReturnType uds_did_write_vin(const uint8_t *data, ErrorCode_t * ErrorCode)
{
    return E_OK; 
}