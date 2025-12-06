#include "uds_service_0x22.h"
#include "../service_did/uds_did_registry.h"
#include "svc_dcm.h"
#include "dcmdsl/dcmdsl.h"
#include "../service_0x27/uds_security_config.h"

CONFIG_LOG_TAG(UDS_0x22, true)

/**
 * @brief Service 0x22 handler - Read Data By Identifier
 */
Std_ReturnType uds_service_0x22_handler(const uds_message_t *message, ErrorCode_t *error_code)
{
    // Phase 1: Validate request length (minimum: SID + 1 DID)
    if (message->request_len < 3) {
        DBG_OUT_E("Invalid message length: %d (minimum 3)", message->request_len);
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }

    // Check if request length is valid (must be SID + N*DIDs)
    if ((message->request_len % 2) == 0) {
        DBG_OUT_E("Invalid message length: %d (must be SID + N*DIDs)", message->request_len);
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }

    // Phase 2: Get current session and security
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
    uint32_t current_security_mask = UDS_SECURITY_MASK_LOCKED;
    
    if (current_level == UDS_SECURITY_LEVEL_1) {
        current_security_mask = UDS_SECURITY_MASK_LEVEL_1;
    } else if (current_level == UDS_SECURITY_LEVEL_2) {
        current_security_mask = UDS_SECURITY_MASK_LEVEL_2;
    }

    // Phase 3: Process each DID
    uint16_t num_dids = (message->request_len - 1) / 2;
    uint16_t response_pos = 0;
    bool at_least_one_did_read = false;

    DBG_OUT_I("RDBI: Processing %d DID(s) in session 0x%02X", num_dids, current_session);

    for (uint16_t i = 0; i < num_dids; i++) {
        uint16_t did = (message->request[1 + (i * 2)] << 8) | message->request[2 + (i * 2)];
        
        // Find DID in registry
        const uds_did_entry_t *did_entry = uds_did_registry_find(did);
        
        if (did_entry == NULL) {
            DBG_OUT_W("DID 0x%04X not found in registry", did);
            // If only one DID requested and it's not found, return error
            if (num_dids == 1) {
                *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
                return E_NOT_OK;
            }
            // Otherwise skip this DID
            continue;
        }

        // Check if DID supports Read service
        if (did_entry->read_config.callback == NULL) {
            DBG_OUT_W("DID 0x%04X does not support Read (0x22)", did);
            if (num_dids == 1) {
                *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
                return E_NOT_OK;
            }
            continue;
        }

        // Validate session and security access
        if (uds_did_validate_access(did, UDS_SID_READ_DATA_BY_IDENTIFIER, current_session_mask, current_security_mask) != E_OK) {
            DBG_OUT_W("DID 0x%04X access denied (session: 0x%08X, security: 0x%08X)", 
                      did, current_session_mask, current_security_mask);
            if (num_dids == 1) {
                // Return proper NRC based on which check failed
                if ((did_entry->read_config.session_mask & current_session_mask) == 0) {
                    *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
                } else {
                    *error_code = UDS_NRC_SECURITY_ACCESS_DENIED;
                }
                return E_NOT_OK;
            }
            continue;
        }

        // Determine actual data length
        uint16_t data_len = did_entry->expected_length;
        
        // For variable length DIDs, call length_getter
        if (data_len == 0 && did_entry->read_config.length_getter != NULL) {
            data_len = did_entry->read_config.length_getter();
            if (data_len == 0) {
                DBG_OUT_E("DID 0x%04X length_getter returned 0", did);
                if (num_dids == 1) {
                    *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
                    return E_NOT_OK;
                }
                continue;
            }
        }
        
        // Check response buffer space (DID + data)
        if (response_pos + 2 + data_len > 256) {
            DBG_OUT_E("Response buffer full (need %d bytes, only %d available)", 
                      2 + data_len, 256 - response_pos);
            if (!at_least_one_did_read) {
                *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
                return E_NOT_OK;
            }
            break;  // Stop processing, return what we have
        }

        // Add DID to response
        message->response[response_pos++] = (did >> 8) & 0xFF;
        message->response[response_pos++] = did & 0xFF;

        // Call DID read callback - it just fills the buffer
        Std_ReturnType result = did_entry->read_config.callback(&message->response[response_pos]);

        if (result == DCM_E_PENDING) {
            // Service pending - will retry
            DBG_OUT_I("DID 0x%04X read pending", did);
            *error_code = UDS_NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING;
            return DCM_E_PENDING;
        }
        else if (result != E_OK) {
            // Read failed - remove DID from response
            response_pos -= 2;
            DBG_OUT_E("DID 0x%04X read failed", did);
            
            if (num_dids == 1) {
                *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
                return E_NOT_OK;
            }
            continue;
        }

        // Success
        response_pos += data_len;
        at_least_one_did_read = true;
        DBG_OUT_I("DID 0x%04X read successfully (%d bytes)", did, data_len);
    }

    // Phase 4: Check if any valid DIDs were read
    if (!at_least_one_did_read || response_pos == 0) {
        DBG_OUT_E("No valid DIDs processed");
        *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
        return E_NOT_OK;
    }

    // Build positive response
    *(message->response_len) = response_pos;
    DBG_OUT_I("RDBI successful - %d bytes", response_pos);
    
    return E_OK;
}
