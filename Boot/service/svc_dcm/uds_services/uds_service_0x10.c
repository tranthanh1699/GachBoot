#include "uds_service_0x10.h"
#include "svc_dcm.h"
#include "dcmdsl/dcmdsl.h"

CONFIG_LOG_TAG(UDS_0x10, true)

/**
 * @brief Service 0x10 handler - Diagnostic Session Control
 */
Std_ReturnType uds_service_0x10_handler(const uds_message_t *message, uint8_t *error_code)
{
    // Phase 1: Parse and validate
    if (message->request_len != 2) {
        DBG_OUT_E("Invalid message length: %d (expected 2)", message->request_len);
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }
    
    uint8_t session_type = message->request[1];
    
    // Phase 2: Validate session type
    if (session_type != UDS_SESSION_DEFAULT && 
        session_type != UDS_SESSION_PROGRAMMING && 
        session_type != UDS_SESSION_EXTENDED_DIAGNOSTIC) {
        DBG_OUT_E("Invalid session type: 0x%02X", session_type);
        *error_code = UDS_NRC_SUBFUNCTION_NOT_SUPPORTED;
        return E_NOT_OK;
    }
    
    // Phase 3: Process - update session via DSL
    dcmdsl_set_session(session_type);
    
    // Get timing parameters
    const dcmdsl_timing_params_t *timing = dcmdsl_get_timing_params();
    
    // Phase 4: Build positive response
    message->response[0] = UDS_SID_DIAGNOSTIC_SESSION_CONTROL + 0x40; // 0x50
    message->response[1] = session_type;
    // P2_Server_Max in units of 1ms (2 bytes, big-endian)
    message->response[2] = (timing->p2_server_max >> 8) & 0xFF;
    message->response[3] = timing->p2_server_max & 0xFF;
    // P2*_Server_Max in units of 10ms (2 bytes, big-endian)
    uint16_t p2_star_units = timing->p2_star_server_max / 10;
    message->response[4] = (p2_star_units >> 8) & 0xFF;
    message->response[5] = p2_star_units & 0xFF;
    
    *(message->response_len) = 6;
    
    DBG_OUT_I("Session changed to: 0x%02X", session_type);
    
    return E_OK;
}
