#ifndef DCM_DID_ACCESS_H
#define DCM_DID_ACCESS_H

#include "DID_PBCfg.h"
#include "DCM_Session_PBCfg.h"
#include "Security_PBCfg.h"

/**
 * @brief Check if DID read operation is allowed
 * @param did_entry DID configuration entry
 * @param current_session_mask Current session mask
 * @param current_security_mask Current security mask
 * @param error_code Output error code if access denied
 * @return E_OK if allowed, E_NOT_OK if denied
 */
Std_ReturnType dcm_did_check_read_access(
    const uds_did_entry_t *did_entry,
    uint32_t current_session_mask,
    uint32_t current_security_mask,
    ErrorCode_t *error_code
);

/**
 * @brief Check if DID write operation is allowed
 * @param did_entry DID configuration entry
 * @param current_session_mask Current session mask
 * @param current_security_mask Current security mask
 * @param error_code Output error code if access denied
 * @return E_OK if allowed, E_NOT_OK if denied
 */
Std_ReturnType dcm_did_check_write_access(
    const uds_did_entry_t *did_entry,
    uint32_t current_session_mask,
    uint32_t current_security_mask,
    ErrorCode_t *error_code
);

/**
 * @brief Validate DID data length for read/write operation
 * @param did_entry DID configuration entry
 * @param is_write true for write, false for read
 * @param data_len Data length to validate
 * @return true if length is valid, false otherwise
 */
bool dcm_did_validate_length(
    const uds_did_entry_t *did_entry,
    bool is_write,
    uint16_t data_len
);

#endif /* DCM_DID_ACCESS_H */
