#include "uds_service_0x3E.h"
#include "svc_dcm.h"

CONFIG_LOG_TAG(UDS_0x3E, false)

/**
 * @brief Service 0x3E handler - Tester Present
 */
Std_ReturnType uds_service_0x3e_handler(const uds_message_t *message, ErrorCode_t *error_code)
{
    // Phase 1: Parse and validate
    if (message->request_len != 2) {
        DBG_OUT_E("Invalid message length: %d (expected 2)", message->request_len);
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }
    
    uint8_t sub_function = message->request[1];
    
    // Phase 2: Validate sub-function
    if ((sub_function & 0x7F) != 0x00) {
        DBG_OUT_E("Invalid sub-function: 0x%02X", sub_function);
        *error_code = UDS_NRC_SUBFUNCTION_NOT_SUPPORTED;
        return E_NOT_OK;
    }
    
    // Phase 3: Check suppress response bit
    bool suppress_response = (sub_function & 0x80) != 0;
    
    if (suppress_response) {
        DBG_OUT_I("Tester Present - Response suppressed");
        *(message->response_len) = 0;
        return E_OK; // Success but no response
    }
    
    // Phase 4: Build positive response (data only, DCMDSP will add positive SID)
    message->response[0] = 0x00;
    *(message->response_len) = 1;
    
    DBG_OUT_I("Tester Present acknowledged");
    
    return E_OK;
}
