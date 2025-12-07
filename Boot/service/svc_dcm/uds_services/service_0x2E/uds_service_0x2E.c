#include "uds_service_0x2E.h"
#include "../service_did/uds_did_registry.h"
#include "svc_dcm.h"
#include "dcmdsl/dcmdsl.h"
#include "../service_0x27/uds_service_0x27.h"
#include "dcm_service_access.h"  // New API layer
#include "dcm_did_access.h"      // New DID access API

CONFIG_LOG_TAG(UDS_0x2E, true)

/**
 * @brief Service 0x2E handler - Write Data By Identifier (WDBI)
 */
Std_ReturnType uds_service_0x2E_handler(const uds_message_t *message, ErrorCode_t *error_code)
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

    // Phase 4: Get current session and security state (using dynamic code gen API)
    uint8_t current_session = dcmdsl_get_session();
    uint8_t current_security_level = uds_security_get_active_level();
    
    // Convert to masks using generated config
    uint32_t current_session_mask = dcm_service_get_session_mask(current_session);
    uint32_t current_security_mask = dcm_service_get_security_mask(current_security_level);
    
    DBG_OUT_I("Access check: Session=0x%02X (mask=0x%08X), Security=0x%02X (mask=0x%08X)", 
              current_session, current_session_mask, current_security_level, current_security_mask);
    
    // Phase 5: Check DID write access (session + security) - BEFORE calling callback
    if (dcm_did_check_write_access(did_entry, current_session_mask, current_security_mask, error_code) != E_OK) {
        DBG_OUT_E("DID 0x%04X write access denied", did);
        return E_NOT_OK;
    }

    // Phase 6: Validate data length
    if (!dcm_did_validate_length(did_entry, true, data_len)) {
        DBG_OUT_E("Invalid data length: %d (expected: %d)", data_len, did_entry->expected_length);
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }

    // Phase 7: Call DID write callback - all validation done (session, security, length checked)
    Std_ReturnType result = did_entry->write_config.callback(data, error_code);

    if (result == DCM_E_PENDING) {
        DBG_OUT_I("DID 0x%04X write pending", did);
        *error_code = UDS_NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING;
        return DCM_E_PENDING;
    }
    else if (result != E_OK) {
        DBG_OUT_E("DID 0x%04X write failed (callback returned error)", did);
        // Callback should set proper error_code
        return E_NOT_OK;
    }

    // Phase 8: Build positive response (echo DID)
    message->response[0] = (did >> 8) & 0xFF;
    message->response[1] = did & 0xFF;
    *(message->response_len) = 2;
    
    DBG_OUT_I("WDBI successful - DID: 0x%04X", did);
    
    return E_OK;
}
