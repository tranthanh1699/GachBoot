#include "uds_service_0x31.h"
#include "Routine_PBCfg.h"
#include "svc_dcm.h"
#include "dcmdsl/dcmdsl.h"
#include "../service_0x27/uds_service_0x27.h"
#include "dcm_service_access.h"

CONFIG_LOG_TAG(UDS_0x31, true)

/**
 * @brief Service 0x31 handler - Routine Control
 */
Std_ReturnType uds_service_0x31_handler(const uds_message_t *message, ErrorCode_t *error_code)
{
    // Phase 1: Validate request length (minimum: SID + SubFunc + RID)
    if (message->request_len < 4) {
        DBG_OUT_E("Invalid message length: %d (minimum 4)", message->request_len);
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }

    // Phase 2: Extract sub-function and RID
    uint8_t sub_function = message->request[1];
    uint16_t rid = (message->request[2] << 8) | message->request[3];
    const uint8_t *option_record = (message->request_len > 4) ? &message->request[4] : NULL;
    uint16_t option_record_len = (message->request_len > 4) ? (message->request_len - 4) : 0;

    // Phase 3: Validate sub-function
    if (sub_function != UDS_ROUTINE_CONTROL_START &&
        sub_function != UDS_ROUTINE_CONTROL_STOP &&
        sub_function != UDS_ROUTINE_CONTROL_REQUEST_RESULTS) {
        DBG_OUT_E("Invalid sub-function: 0x%02X", sub_function);
        *error_code = UDS_NRC_SUBFUNCTION_NOT_SUPPORTED;
        return E_NOT_OK;
    }

    // Phase 4: Find routine in registry
    const uds_routine_entry_t *routine_entry = uds_routine_find_entry(rid);
    
    if (routine_entry == NULL) {
        DBG_OUT_W("RID 0x%04X not found in registry", rid);
        *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
        return E_NOT_OK;
    }

    // Phase 4.5: Validate sub-function is supported
    uint8_t sf_bit = 0;
    if (sub_function == UDS_ROUTINE_CONTROL_START) {
        sf_bit = (1 << 0);
    } else if (sub_function == UDS_ROUTINE_CONTROL_STOP) {
        sf_bit = (1 << 1);
    } else if (sub_function == UDS_ROUTINE_CONTROL_REQUEST_RESULTS) {
        sf_bit = (1 << 2);
    }
    
    if ((routine_entry->supported_subfunctions & sf_bit) == 0) {
        DBG_OUT_W("RID 0x%04X does not support sub-function 0x%02X", rid, sub_function);
        *error_code = UDS_NRC_SUBFUNCTION_NOT_SUPPORTED;
        return E_NOT_OK;
    }

    // Phase 4.6: Validate option_record length
    if (!uds_routine_validate_option_length(routine_entry, sub_function, option_record_len)) {
        uint16_t expected_len = 0;
        if (sub_function == UDS_ROUTINE_CONTROL_START) {
            expected_len = routine_entry->start_option_len;
        } else if (sub_function == UDS_ROUTINE_CONTROL_STOP) {
            expected_len = routine_entry->stop_option_len;
        } else if (sub_function == UDS_ROUTINE_CONTROL_REQUEST_RESULTS) {
            expected_len = routine_entry->results_option_len;
        }
        
        DBG_OUT_E("RID 0x%04X invalid option length: expected %u, got %u", 
                  rid, expected_len, option_record_len);
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }

    // Phase 5: Get current session and security (using dynamic code gen API)
    uint8_t current_session = dcmdsl_get_session();
    uint8_t current_security_level = uds_security_get_active_level();
    
    // Convert to masks using generated config
    uint32_t current_session_mask = dcm_service_get_session_mask(current_session);
    uint32_t current_security_mask = dcm_service_get_security_mask(current_security_level);

    // Phase 6: Check session support
    if ((routine_entry->session_mask & current_session_mask) == 0) {
        DBG_OUT_E("RID 0x%04X not supported in session 0x%02X (mask=0x%08X)", rid, current_session, current_session_mask);
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }

    // Phase 7: Check security access
    if ((routine_entry->security_mask & current_security_mask) == 0) {
        DBG_OUT_E("RID 0x%04X requires security access (mask=0x%08X)", rid, current_security_mask);
        *error_code = UDS_NRC_SECURITY_ACCESS_DENIED;
        return E_NOT_OK;
    }

    // Phase 7: Call routine callback
    uint8_t status_record[256];
    memset(status_record, 0, sizeof(status_record));
    uint16_t status_record_len = 0;
    
    Std_ReturnType result = routine_entry->callback(sub_function, option_record, option_record_len,
                                                     status_record, &status_record_len);

    if (result == DCM_E_PENDING) {
        *error_code = UDS_NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING;
        return DCM_E_PENDING;
    }
    else if (result != E_OK) {
        DBG_OUT_E("RID 0x%04X execution failed", rid);
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }

    // Phase 7.5: Validate status_record length
    uint16_t expected_status_len = 0;
    if (sub_function == UDS_ROUTINE_CONTROL_START) {
        expected_status_len = routine_entry->start_status_len;
    } else if (sub_function == UDS_ROUTINE_CONTROL_STOP) {
        expected_status_len = routine_entry->stop_status_len;
    } else if (sub_function == UDS_ROUTINE_CONTROL_REQUEST_RESULTS) {
        expected_status_len = routine_entry->results_status_len;
    }
    
    // Check if callback returned correct status length (if configured, 0 = variable length allowed)
    if (expected_status_len > 0 && status_record_len != expected_status_len) {
        DBG_OUT_W("RID 0x%04X returned wrong status length: expected %u, got %u", 
                  rid, expected_status_len, status_record_len);
        // Note: Some implementations may return variable length, so this is a warning not error
    }
    
    // Validate status_record_len doesn't overflow response buffer
    if (status_record_len > 253) {  // Max: 256 (UDS buffer) - 3 (SID + RID bytes)
        DBG_OUT_E("RID 0x%04X status record too long: %u bytes (max 253)", rid, status_record_len);
        *error_code = UDS_NRC_RESPONSE_TOO_LONG;
        return E_NOT_OK;
    }

    // Phase 8: Build positive response (SubFunc + RID + StatusRecord)
    message->response[0] = sub_function;
    message->response[1] = (rid >> 8) & 0xFF;
    message->response[2] = rid & 0xFF;
    
    // Copy status record
    if (status_record_len > 0 && status_record_len <= 253) {
        memcpy(&message->response[3], status_record, status_record_len);
    }
    
    *(message->response_len) = 3 + status_record_len;
    
    DBG_OUT_I("Routine Control successful - RID: 0x%04X, Status Length: %d", rid, status_record_len);
    
    return E_OK;
}
