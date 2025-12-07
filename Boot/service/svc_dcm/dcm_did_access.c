#include "dcm_did_access.h"

/* NRC codes */
#define UDS_NRC_CONDITIONS_NOT_CORRECT          0x22u
#define UDS_NRC_SECURITY_ACCESS_DENIED          0x33u
#define UDS_NRC_INCORRECT_MESSAGE_LENGTH        0x13u

/**
 * @brief Check if DID read operation is allowed
 */
Std_ReturnType dcm_did_check_read_access(
    const uds_did_entry_t *did_entry,
    uint32_t current_session_mask,
    uint32_t current_security_mask,
    ErrorCode_t *error_code
)
{
    if (did_entry == NULL) {
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }
    
    // Check if read is supported
    if (did_entry->read_config.callback == NULL) {
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }
    
    // Check session support
    if ((did_entry->read_config.session_mask & current_session_mask) == 0) {
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }
    
    // Check security level (if required)
    if (did_entry->read_config.security_mask != 0) {
        if ((did_entry->read_config.security_mask & current_security_mask) == 0) {
            *error_code = UDS_NRC_SECURITY_ACCESS_DENIED;
            return E_NOT_OK;
        }
    }
    
    return E_OK;
}

/**
 * @brief Check if DID write operation is allowed
 */
Std_ReturnType dcm_did_check_write_access(
    const uds_did_entry_t *did_entry,
    uint32_t current_session_mask,
    uint32_t current_security_mask,
    ErrorCode_t *error_code
)
{
    if (did_entry == NULL) {
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }
    
    // Check if write is supported
    if (did_entry->write_config.callback == NULL) {
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }
    
    // Check session support
    if ((did_entry->write_config.session_mask & current_session_mask) == 0) {
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }
    
    // Check security level (if required)
    if (did_entry->write_config.security_mask != 0) {
        if ((did_entry->write_config.security_mask & current_security_mask) == 0) {
            *error_code = UDS_NRC_SECURITY_ACCESS_DENIED;
            return E_NOT_OK;
        }
    }
    
    return E_OK;
}

/**
 * @brief Validate DID data length for read/write operation
 */
bool dcm_did_validate_length(
    const uds_did_entry_t *did_entry,
    bool is_write,
    uint16_t data_len
)
{
    if (did_entry == NULL) {
        return false;
    }
    
    // Fixed length (expected_length != 0) - must match exactly
    if (did_entry->expected_length != 0) {
        return (data_len == did_entry->expected_length);
    }
    
    // Variable length (expected_length == 0) - check range
    return (data_len >= did_entry->min_length && 
            data_len <= did_entry->max_length);
}
