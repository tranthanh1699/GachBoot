#ifndef DCM_SERVICE_ACCESS_H
#define DCM_SERVICE_ACCESS_H

#include "Service_PBCfg.h"
#include "DCM_Session_PBCfg.h"
#include "Security_PBCfg.h"

/**
 * @brief Get current session mask from active session value
 * @param session_value Current session value (from dcmdsl_get_session())
 * @return Session mask for access control
 */
uint32_t dcm_service_get_session_mask(uint8_t session_value);

/**
 * @brief Get current security mask from active security level
 * @param security_level Current security level (from uds_security_get_active_level())
 * @return Security mask for access control
 */
uint32_t dcm_service_get_security_mask(uint8_t security_level);

/**
 * @brief Check if service is allowed in current session and security level
 * @param service_id Service ID to check
 * @param current_session_mask Current session mask
 * @param current_security_mask Current security mask
 * @param error_code Output error code if access denied
 * @return E_OK if allowed, E_NOT_OK if denied
 */
Std_ReturnType dcm_service_check_access(
    uint8_t service_id,
    uint32_t current_session_mask,
    uint32_t current_security_mask,
    ErrorCode_t *error_code
);

/**
 * @brief Find service configuration by service ID
 * @param service_id Service ID to find
 * @return Pointer to service config or NULL if not found
 */
const dcm_service_config_t* dcm_service_find_config(uint8_t service_id);

#endif /* DCM_SERVICE_ACCESS_H */
