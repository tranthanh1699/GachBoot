#include "dcm_service_access.h"

/* NRC codes - should match your UDS definitions */
#define UDS_NRC_SERVICE_NOT_SUPPORTED           0x11u
#define UDS_NRC_CONDITIONS_NOT_CORRECT          0x22u
#define UDS_NRC_SECURITY_ACCESS_DENIED          0x33u

/**
 * @brief Convert session value to session mask using generated config
 */
uint32_t dcm_service_get_session_mask(uint8_t session_value)
{
    // Search in generated session table
    for (uint8_t i = 0; i < SVC_DCM_SESSION_COUNT; i++) {
        if (svc_dcm_session_table[i].session_value == session_value) {
            return svc_dcm_session_table[i].session_mask;  // Return mask from table
        }
    }
    
    // Default session if not found
    return DCM_DEFAULT_SESSION_MASK;  // Use generated default mask
}

/**
 * @brief Convert security level to security mask using generated config
 */
uint32_t dcm_service_get_security_mask(uint8_t security_level)
{
    if (security_level == 0) {
        return 0x00000001u;  // Locked state (bit 0)
    }
    
    // Search in generated security table
    for (uint8_t i = 0; i < SECURITY_LEVEL_COUNT; i++) {
        if (security_level_config_table[i].security_level == security_level) {
            return (1u << security_level);  // Convert level to mask
        }
    }
    
    return 0x00000001u;  // Default to locked
}

/**
 * @brief Find service configuration by service ID
 */
const dcm_service_config_t* dcm_service_find_config(uint8_t service_id)
{
    for (uint8_t i = 0; i < DCM_SERVICE_COUNT; i++) {
        if (dcm_service_config_table[i].service_id == service_id) {
            return &dcm_service_config_table[i];
        }
    }
    return NULL;
}

/**
 * @brief Check if service is allowed in current session and security level
 */
Std_ReturnType dcm_service_check_access(
    uint8_t service_id,
    uint32_t current_session_mask,
    uint32_t current_security_mask,
    ErrorCode_t *error_code
)
{
    // Find service configuration
    const dcm_service_config_t *service = dcm_service_find_config(service_id);
    
    if (service == NULL) {
        *error_code = UDS_NRC_SERVICE_NOT_SUPPORTED;
        return E_NOT_OK;
    }
    
    // Check session support
    if ((service->session_mask & current_session_mask) == 0) {
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }
    
    // Check security level (if service requires security)
    if (service->security_mask != 0) {
        if ((service->security_mask & current_security_mask) == 0) {
            *error_code = UDS_NRC_SECURITY_ACCESS_DENIED;
            return E_NOT_OK;
        }
    }
    
    return E_OK;
}
