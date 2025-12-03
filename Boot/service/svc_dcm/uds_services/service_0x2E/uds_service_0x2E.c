#include "uds_service_0x2E.h"
#include "../service_did/uds_did_registry.h"
#include "svc_dcm.h"
#include "dcmdsl/dcmdsl.h"
#include "../service_0x27/uds_security_config.h"

CONFIG_LOG_TAG(UDS_0x2E, true)

/**
 * @brief Service 0x2E handler - Write Data By Identifier
 */
Std_ReturnType uds_service_0x2e_handler(const uds_message_t *message, uint8_t *error_code)
{
    // Phase 1: Validate request length (minimum: SID + DID + 1 byte data)
    if (message->request_len < 4) {
        DBG_OUT_E("Invalid message length: %d (minimum 4)", message->request_len);
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }

    // Phase 2: Extract DID and data
    uint16_t did = (message->request[1] << 8) | message->request[2];
    const uint8_t *data = &message->request[3];
    uint16_t data_len = message->request_len - 3;

    DBG_OUT_I("WDBI: DID 0x%04X, Data Length: %d", did, data_len);

    // Phase 3: Find DID in registry
    const uds_did_entry_t *did_entry = uds_did_registry_find(did);
    
    if (did_entry == NULL) {
        DBG_OUT_W("DID 0x%04X not found in registry", did);
        *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
        return E_NOT_OK;
    }

    // Check if DID supports Write service
    if (did_entry->write_config.callback == NULL) {
        DBG_OUT_W("DID 0x%04X does not support Write (0x2E)", did);
        *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
        return E_NOT_OK;
    }

    // Phase 4: Check session and security support
    uint8_t current_session = dcmdsl_get_session();
    uint32_t current_session_mask = 0;
    switch (current_session) {
        case UDS_SESSION_DEFAULT:
            current_session_mask = UDS_SESSION_MASK_DEFAULT;
            break;
        case UDS_SESSION_PROGRAMMING:
            current_session_mask = UDS_SESSION_MASK_PROGRAMMING;
            break;
        case UDS_SESSION_EXTENDED_DIAGNOSTIC:
            current_session_mask = UDS_SESSION_MASK_EXTENDED;
            break;
        default:
            current_session_mask = UDS_SESSION_MASK_DEFAULT;
            break;
    }
    
    // Get current security level and convert to mask
    uint8_t current_level = uds_security_get_active_level();
    uint32_t current_security_mask = UDS_SECURITY_MASK_LOCKED;  // Default: locked
    
    if (current_level == UDS_SECURITY_LEVEL_1) {
        current_security_mask = UDS_SECURITY_MASK_LEVEL_1;
    } else if (current_level == UDS_SECURITY_LEVEL_2) {
        current_security_mask = UDS_SECURITY_MASK_LEVEL_2;
    }
    
    // Validate session and security access
    if (uds_did_validate_access(did, UDS_SID_WRITE_DATA_BY_IDENTIFIER, current_session_mask, current_security_mask) != E_OK) {
        DBG_OUT_E("DID 0x%04X access denied (session: 0x%08X, security: 0x%08X)", 
                  did, current_session_mask, current_security_mask);
        // Return proper NRC based on which check failed
        if ((did_entry->write_config.session_mask & current_session_mask) == 0) {
            *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        } else {
            *error_code = UDS_NRC_SECURITY_ACCESS_DENIED;
        }
        return E_NOT_OK;
    }

    // Phase 5: Validate data length
    if (!uds_did_validate_length(did, UDS_SID_WRITE_DATA_BY_IDENTIFIER, data_len)) {
        DBG_OUT_E("Invalid data length: %d", data_len);
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }

    // Phase 6: Call DID write callback - all validation done, just write
    Std_ReturnType result = did_entry->write_config.callback(data, data_len);

    if (result == DCM_E_PENDING) {
        DBG_OUT_I("DID 0x%04X write pending", did);
        *error_code = UDS_NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING;
        return DCM_E_PENDING;
    }
    else if (result != E_OK) {
        DBG_OUT_E("DID 0x%04X write failed", did);
        // Check if semantic validation is enabled for better error reporting
        if (did_entry->write_config.semantic_validation) {
            *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;  // Invalid data semantics
        } else {
            *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;  // Write operation failed
        }
        return E_NOT_OK;
    }

    // Phase 7: Build positive response (echo DID)
    message->response[0] = (did >> 8) & 0xFF;
    message->response[1] = did & 0xFF;
    *(message->response_len) = 2;
    
    DBG_OUT_I("WDBI successful - DID: 0x%04X", did);
    
    return E_OK;
}
