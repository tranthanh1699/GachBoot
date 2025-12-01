#include "uds_service_0x2E.h"
#include "uds_wdbi_did_registry.h"
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
    const uds_wdbi_did_entry_t *did_entry = uds_wdbi_find_did(did);
    
    if (did_entry == NULL) {
        DBG_OUT_W("DID 0x%04X not found in write registry", did);
        *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
        return E_NOT_OK;
    }

    // Phase 4: Check session and security support
    uint8_t current_session = dcmdsl_get_active_session();
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

    if ((did_entry->session_mask & current_session_mask) == 0) {
        DBG_OUT_E("DID 0x%04X not supported in session 0x%02X (mask: 0x%08X, required: 0x%08X)", 
                  did, current_session, current_session_mask, did_entry->session_mask);
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }
    
    // Get current security level and convert to mask
    uint8_t current_level = uds_security_get_active_level();
    uint32_t current_security_mask = UDS_SECURITY_MASK_LOCKED;  // Default: locked
    
    if (current_level == UDS_SECURITY_LEVEL_1) {
        current_security_mask = UDS_SECURITY_MASK_LEVEL_1;
    } else if (current_level == UDS_SECURITY_LEVEL_2) {
        current_security_mask = UDS_SECURITY_MASK_LEVEL_2;
    }
    
    if ((did_entry->security_mask & current_security_mask) == 0) {
        DBG_OUT_E("DID 0x%04X requires security access (mask: 0x%08X, required: 0x%08X)", 
                  did, current_security_mask, did_entry->security_mask);
        *error_code = UDS_NRC_SECURITY_ACCESS_DENIED;
        return E_NOT_OK;
    }

    // Phase 5: Validate data length
    if (did_entry->expected_length != 0) {
        // Fixed length DID - must match exactly
        if (data_len != did_entry->expected_length) {
            DBG_OUT_E("Invalid data length: %d (expected %d)", data_len, did_entry->expected_length);
            *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
            return E_NOT_OK;
        }
    } else {
        // Variable length DID - check min/max bounds
        if (data_len < did_entry->min_length || data_len > did_entry->max_length) {
            DBG_OUT_E("Data length %d out of range (min: %d, max: %d)", 
                      data_len, did_entry->min_length, did_entry->max_length);
            *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
            return E_NOT_OK;
        }
    }

    // Phase 6: Call DID write callback - all validation done, just write
    Std_ReturnType result = did_entry->write_callback(data, data_len);

    if (result == DCM_E_PENDING) {
        DBG_OUT_I("DID 0x%04X write pending", did);
        *error_code = UDS_NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING;
        return DCM_E_PENDING;
    }
    else if (result != E_OK) {
        DBG_OUT_E("DID 0x%04X write failed", did);
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }

    // Phase 7: Build positive response (echo DID)
    message->response[0] = (did >> 8) & 0xFF;
    message->response[1] = did & 0xFF;
    *(message->response_len) = 2;
    
    DBG_OUT_I("WDBI successful - DID: 0x%04X", did);
    
    return E_OK;
}
