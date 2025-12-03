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
#include "uds_did_callbacks.h"
#include "dev_common.h"
#include "svc_dcm.h"
#include <string.h>

CONFIG_LOG_TAG(DID_REG, true)

/* ========================================================================== */
/*                           DID Registry Table                               */
/* ========================================================================== */

/**
 * @brief Unified DID Registry
 * 
 * Each entry configures a DID with support for multiple services (0x22, 0x2E, 0x2F).
 * NULL callbacks indicate service not supported for that DID.
 * 
 * Format:
 * {
 *   DID, expected_length, min_length, max_length,
 *   
 *   // Service 0x22 (Read) config
 *   {read_callback, length_getter, session_mask, security_mask},
 *   
 *   // Service 0x2E (Write) config
 *   {write_callback, session_mask, security_mask, semantic_validation},
 *   
 *   // Service 0x2F (IO Control) config - Future
 *   {io_control_callback, session_mask, security_mask, supported_options}
 * }
 */
static const uds_did_entry_t did_registry[] = {
    /* ====================================================================== */
    /* DID 0xF190: VIN (Vehicle Identification Number)                       */
    /* - Read: All sessions, no security                                     */
    /* - Write: Not supported                                                */
    /* ====================================================================== */
    {
        .did = 0xF190,
        .expected_length = 17,      // Fixed 17 bytes
        .min_length = 17,
        .max_length = 17,
        
        .read_config = {
            .callback = did_read_vin,
            .length_getter = NULL,  // Fixed length
            .session_mask = UDS_SESSION_MASK_ALL,
            .security_mask = UDS_SECURITY_MASK_ALL
        },
        
        .write_config = {
            .callback = NULL,       // Read-only DID
            .session_mask = 0,
            .security_mask = 0,
            .semantic_validation = false
        },
        
        .io_control_config = {
            .callback = NULL,
            .session_mask = 0,
            .security_mask = 0,
            .supported_options = 0
        }
    },
    
    /* ====================================================================== */
    /* DID 0xF183: Boot Software ID                                          */
    /* - Read: All sessions, no security                                     */
    /* - Write: Not supported                                                */
    /* ====================================================================== */
    {
        .did = 0xF183,
        .expected_length = 11,
        .min_length = 11,
        .max_length = 11,
        
        .read_config = {
            .callback = did_read_boot_sw_id,
            .length_getter = NULL,
            .session_mask = UDS_SESSION_MASK_ALL,
            .security_mask = UDS_SECURITY_MASK_ALL
        },
        
        .write_config = {
            .callback = NULL,
            .session_mask = 0,
            .security_mask = 0,
            .semantic_validation = false
        },
        
        .io_control_config = {
            .callback = NULL,
            .session_mask = 0,
            .security_mask = 0,
            .supported_options = 0
        }
    },
    
    /* ====================================================================== */
    /* DID 0xF184: Application Software ID                                   */
    /* - Read: All sessions, no security                                     */
    /* - Write: Not supported                                                */
    /* ====================================================================== */
    {
        .did = 0xF184,
        .expected_length = 10,
        .min_length = 10,
        .max_length = 10,
        
        .read_config = {
            .callback = did_read_app_sw_id,
            .length_getter = NULL,
            .session_mask = UDS_SESSION_MASK_ALL,
            .security_mask = UDS_SECURITY_MASK_ALL
        },
        
        .write_config = {
            .callback = NULL,
            .session_mask = 0,
            .security_mask = 0,
            .semantic_validation = false
        },
        
        .io_control_config = {
            .callback = NULL,
            .session_mask = 0,
            .security_mask = 0,
            .supported_options = 0
        }
    },
    
    /* ====================================================================== */
    /* DID 0xF18C: ECU Serial Number                                         */
    /* - Read: Default/Extended sessions, no security                        */
    /* - Write: Not supported                                                */
    /* ====================================================================== */
    {
        .did = 0xF18C,
        .expected_length = 4,
        .min_length = 4,
        .max_length = 4,
        
        .read_config = {
            .callback = did_read_ecu_serial,
            .length_getter = NULL,
            .session_mask = UDS_SESSION_MASK_DEFAULT | UDS_SESSION_MASK_EXTENDED,
            .security_mask = UDS_SECURITY_MASK_ALL
        },
        
        .write_config = {
            .callback = NULL,
            .session_mask = 0,
            .security_mask = 0,
            .semantic_validation = false
        },
        
        .io_control_config = {
            .callback = NULL,
            .session_mask = 0,
            .security_mask = 0,
            .supported_options = 0
        }
    },
    
    /* ====================================================================== */
    /* DID 0xF15A: Programming Fingerprint                                   */
    /* - Read: Not supported                                                 */
    /* - Write: Programming/Extended sessions, Level 1 or 2 security         */
    /*   Variable length (1-32 bytes)                                        */
    /* ====================================================================== */
    {
        .did = 0xF15A,
        .expected_length = 0,       // Variable length
        .min_length = 1,
        .max_length = 32,
        
        .read_config = {
            .callback = NULL,       // Write-only DID
            .length_getter = NULL,
            .session_mask = 0,
            .security_mask = 0
        },
        
        .write_config = {
            .callback = did_write_fingerprint,
            .session_mask = UDS_SESSION_MASK_PROGRAMMING | UDS_SESSION_MASK_EXTENDED,
            .security_mask = UDS_SECURITY_MASK_LEVEL_1 | UDS_SECURITY_MASK_LEVEL_2,
            .semantic_validation = false
        },
        
        .io_control_config = {
            .callback = NULL,
            .session_mask = 0,
            .security_mask = 0,
            .supported_options = 0
        }
    },
    
    /* ====================================================================== */
    /* DID 0xF199: Programming Date                                          */
    /* - Read: Not supported                                                 */
    /* - Write: Programming session, Level 2 security                        */
    /*   Fixed 4 bytes (YYYY/MM/DD)                                          */
    /* ====================================================================== */
    {
        .did = 0xF199,
        .expected_length = 4,
        .min_length = 4,
        .max_length = 4,
        
        .read_config = {
            .callback = NULL,
            .length_getter = NULL,
            .session_mask = 0,
            .security_mask = 0
        },
        
        .write_config = {
            .callback = did_write_programming_date,
            .session_mask = UDS_SESSION_MASK_PROGRAMMING,
            .security_mask = UDS_SECURITY_MASK_LEVEL_2,
            .semantic_validation = true     // Validates date format
        },
        
        .io_control_config = {
            .callback = NULL,
            .session_mask = 0,
            .security_mask = 0,
            .supported_options = 0
        }
    },
    
    /* ====================================================================== */
    /* DID 0xF100: ECU Configuration                                         */
    /* - Read: Extended session, no security (Future)                        */
    /* - Write: Extended session, Level 1 or 2 security                      */
    /*   Fixed 2 bytes                                                       */
    /* ====================================================================== */
    {
        .did = 0xF100,
        .expected_length = 2,
        .min_length = 2,
        .max_length = 2,
        
        .read_config = {
            .callback = did_read_ecu_config,  // Future: add callback
            .length_getter = NULL,
            .session_mask = UDS_SESSION_MASK_EXTENDED,
            .security_mask = UDS_SECURITY_MASK_ALL
        },
        
        .write_config = {
            .callback = did_write_ecu_config,
            .session_mask = UDS_SESSION_MASK_EXTENDED,
            .security_mask = UDS_SECURITY_MASK_LEVEL_1 | UDS_SECURITY_MASK_LEVEL_2,
            .semantic_validation = true     // Validates config range
        },
        
        .io_control_config = {
            .callback = NULL,
            .session_mask = 0,
            .security_mask = 0,
            .supported_options = 0
        }
    }
};

#define DID_REGISTRY_COUNT (sizeof(did_registry) / sizeof(uds_did_entry_t))

/* ========================================================================== */
/*                         Registry Access Functions                          */
/* ========================================================================== */

/**
 * @brief Find DID entry in registry
 */
const uds_did_entry_t* uds_did_registry_find(uint16_t did)
{
    for (uint16_t i = 0; i < DID_REGISTRY_COUNT; i++) {
        if (did_registry[i].did == did) {
            return &did_registry[i];
        }
    }
    
    DBG_OUT_W("[DID Registry] DID 0x%04X not found", did);
    return NULL;
}

/**
 * @brief Get total number of DIDs in registry
 */
uint16_t uds_did_registry_get_count(void)
{
    return DID_REGISTRY_COUNT;
}

/**
 * @brief Check if DID supports specific service
 */
bool uds_did_supports_service(uint16_t did, uint8_t service)
{
    const uds_did_entry_t *entry = uds_did_registry_find(did);
    if (entry == NULL) {
        return false;
    }
    
    switch (service) {
        case UDS_SID_READ_DATA_BY_IDENTIFIER:
            return (entry->read_config.callback != NULL);
            
        case UDS_SID_WRITE_DATA_BY_IDENTIFIER:
            return (entry->write_config.callback != NULL);
            
        case UDS_SID_IO_CONTROL_BY_IDENTIFIER:
            return (entry->io_control_config.callback != NULL);
            
        default:
            return false;
    }
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
            if (entry->io_control_config.callback == NULL) {
                return E_NOT_OK;
            }
            required_session_mask = entry->io_control_config.session_mask;
            required_security_mask = entry->io_control_config.security_mask;
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
    if (required_security_mask != UDS_SECURITY_MASK_LOCKED && required_security_mask != UDS_SECURITY_MASK_ALL) {
        if ((security_mask & required_security_mask) == 0) {
            DBG_OUT_W("[DID Registry] DID 0x%04X service 0x%02X: Security access denied", did, service);
            return E_NOT_OK;
        }
    }
    
    return E_OK;
}

/**
 * @brief Get DID length (handles both fixed and variable length)
 */
uint16_t uds_did_get_length(uint16_t did, uint8_t service)
{
    const uds_did_entry_t *entry = uds_did_registry_find(did);
    if (entry == NULL) {
        return 0;
    }
    
    // For read service with variable length, call length getter
    if (service == UDS_SID_READ_DATA_BY_IDENTIFIER) {
        if (entry->expected_length == 0 && entry->read_config.length_getter != NULL) {
            return entry->read_config.length_getter();
        }
    }
    
    // Return expected length (0 for variable)
    return entry->expected_length;
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
