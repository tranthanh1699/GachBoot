#include "dcmdsd.h"
#include "svc_dcm.h"
#include "dcmdsp/dcmdsp.h"
#include <string.h>

CONFIG_LOG_TAG(DCMDSD, true)

// Pending request state
static dcmdsd_pending_state_t pending_state = {0};

/**
 * @brief Get system tick in milliseconds
 */
uint32_t dcmdsd_get_tick_ms(void)
{
    extern uint32_t HAL_GetTick(void);
    return HAL_GetTick();
}

/**
 * @brief Initialize DSD layer
 */
dev_err_t dcmdsd_init(void)
{
    memset(&pending_state, 0, sizeof(pending_state));
    DBG_OUT_I("DCMDSD Initialized");
    return DEV_OK;
}

/**
 * @brief Process pending request (call periodically from main loop or task)
 */
void dcmdsd_process_pending(void)
{
    if (!pending_state.is_pending) {
        return;  // No pending request
    }
    
    uint32_t current_time = dcmdsd_get_tick_ms();
    
    // Check if it's time to retry callback (every 10ms)
    uint32_t retry_elapsed = current_time - pending_state.last_retry_time_ms;
    if (retry_elapsed < DCMDSD_PENDING_CALLBACK_RETRY_MS) {
        return;  // Not yet time to retry callback
    }
    
    // Update retry timestamp
    pending_state.last_retry_time_ms = current_time;
    
    // Prepare response buffer
    uint8_t response_buffer[256];
    uint16_t response_len = 0;
    uint8_t error_code = 0;
    
    // Prepare message structure
    uds_message_t message = {
        .request = pending_state.request_buffer,
        .request_len = pending_state.request_len,
        .response = response_buffer,
        .response_len = &response_len
    };
    
    // Retry service handler (callback is called here)
    Std_ReturnType err = dcmdsp_process_service(pending_state.service_id, &message, &error_code);
    
    if (err == DCM_E_PENDING) {
        // Still pending - check if we need to send NRC 0x78
        uint32_t nrc78_elapsed = current_time - pending_state.last_nrc78_time_ms;
        
        if (nrc78_elapsed >= DCMDSD_PENDING_NRC78_INTERVAL_MS) {
            // Time to send another NRC 0x78
            
            // Check if max NRC 0x78 count exceeded
            if (pending_state.nrc78_count >= DCMDSD_MAX_PENDING_NRC78_COUNT) {
                DBG_OUT_E("Max NRC 0x78 count exceeded - sending NRC 0x10 (General Reject)");
                dcmdsd_send_negative_response(pending_state.service_id, UDS_NRC_GENERAL_REJECT, pending_state.target_address);
                
                // Clear pending state
                memset(&pending_state, 0, sizeof(pending_state));
                return;
            }
            
            // Send NRC 0x78
            pending_state.nrc78_count++;
            pending_state.last_nrc78_time_ms = current_time;
            
            DBG_OUT_I("Service 0x%02X still pending - sending NRC 0x78 (%d/%d)", 
                      pending_state.service_id, pending_state.nrc78_count, DCMDSD_MAX_PENDING_NRC78_COUNT);
            
            dcmdsp_build_negative_response(pending_state.service_id, UDS_NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING, 
                                           response_buffer, &response_len);
            
            dev_com_tp_sdu_t response_sdu;
            response_sdu.Address = pending_state.target_address;
            response_sdu.SduBuffer = response_buffer;
            response_sdu.SduSize = response_len;
            dev_com_tp_transmit(&response_sdu);
        }
        // Else: Still pending but not yet time to send NRC 0x78, will retry callback in 10ms
    }
    else if (err == E_NOT_OK) {
        // Service handler returned error
        DBG_OUT_W("Pending service 0x%02X returned error - NRC: 0x%02X", pending_state.service_id, error_code);
        
        dev_com_tp_sdu_t response_sdu;
        response_sdu.Address = pending_state.target_address;
        response_sdu.SduBuffer = response_buffer;
        response_sdu.SduSize = response_len;
        dev_com_tp_transmit(&response_sdu);
        
        // Clear pending state
        memset(&pending_state, 0, sizeof(pending_state));
    }
    else {
        // Success - send positive response
        DBG_OUT_I("Pending service 0x%02X completed successfully", pending_state.service_id);
        
        dev_com_tp_sdu_t response_sdu;
        response_sdu.Address = pending_state.target_address;
        response_sdu.SduBuffer = response_buffer;
        response_sdu.SduSize = response_len;
        dev_com_tp_transmit(&response_sdu);
        
        // Clear pending state
        memset(&pending_state, 0, sizeof(pending_state));
    }
}

/**
 * @brief Process diagnostic request - dispatch to appropriate service
 */
dev_err_t dcmdsd_process_request(dev_com_tp_sdu_t * sdu_info_p)
{
    DEV_RETURN_ON_FALSE(sdu_info_p != NULL, DEV_ERR_INVALID_ARG, "SDU Info pointer is NULL");
    DEV_RETURN_ON_FALSE(sdu_info_p->SduBuffer != NULL, DEV_ERR_INVALID_ARG, "SDU Buffer is NULL");
    DEV_RETURN_ON_FALSE(sdu_info_p->SduSize > 0, DEV_ERR_INVALID_ARG, "SDU Size is zero");
    
    // If there's already a pending request, reject new request with NRC 0x21 (Busy Repeat Request)
    if (pending_state.is_pending) {
        DBG_OUT_W("Busy - rejecting new request while pending");
        dcmdsd_send_negative_response(sdu_info_p->SduBuffer[0], 0x21, sdu_info_p->Address);
        return DEV_OK;
    }
    
    uint8_t sid = sdu_info_p->SduBuffer[0];
    DBG_OUT_I("Dispatching SID: 0x%02X, Size: %d", sid, sdu_info_p->SduSize);
    
    // Prepare response buffer
    uint8_t response_buffer[256];
    uint16_t response_len = 0;
    uint8_t error_code = 0;
    
    // Prepare message structure
    uds_message_t message = {
        .request = sdu_info_p->SduBuffer,
        .request_len = sdu_info_p->SduSize,
        .response = response_buffer,
        .response_len = &response_len
    };
    
    // Dispatch to DSP layer unified processor
    Std_ReturnType err = dcmdsp_process_service(sid, &message, &error_code);
    
    if (err == DCM_E_PENDING) {
        // Service is pending - store request for retry and send NRC 0x78
        DBG_OUT_I("Service 0x%02X pending - storing request and sending NRC 0x78", sid);
        
        pending_state.is_pending = true;
        pending_state.service_id = sid;
        pending_state.target_address = sdu_info_p->Address;
        pending_state.request_len = sdu_info_p->SduSize;
        memcpy(pending_state.request_buffer, sdu_info_p->SduBuffer, sdu_info_p->SduSize);
        pending_state.nrc78_count = 1;
        pending_state.last_nrc78_time_ms = dcmdsd_get_tick_ms();
        pending_state.last_retry_time_ms = dcmdsd_get_tick_ms();
        
        // Send first NRC 0x78
        dev_com_tp_sdu_t response_sdu;
        response_sdu.Address = sdu_info_p->Address;
        response_sdu.SduBuffer = response_buffer;
        response_sdu.SduSize = response_len;
        dev_com_tp_transmit(&response_sdu);
        
        return DEV_OK;
    }
    else if (err == E_NOT_OK) {
        // Service not supported or handler returned error
        if (error_code == 0) {
            // No error code set - service not in table
            DBG_OUT_W("Service Not Supported: 0x%02X", sid);
            dcmdsd_send_negative_response(sid, UDS_NRC_SERVICE_NOT_SUPPORTED, sdu_info_p->Address);
        } else {
            // Error code already set by handler - response already built
            dev_com_tp_sdu_t response_sdu;
            response_sdu.Address = sdu_info_p->Address;
            response_sdu.SduBuffer = response_buffer;
            response_sdu.SduSize = response_len;
            dev_com_tp_transmit(&response_sdu);
        }
        return DEV_OK;
    }
    
    // Send response if generated (E_OK case)
    if (response_len > 0) {
        dev_com_tp_sdu_t response_sdu;
        response_sdu.Address = sdu_info_p->Address;
        response_sdu.SduBuffer = response_buffer;
        response_sdu.SduSize = response_len;
        dev_com_tp_transmit(&response_sdu);
    }
    
    return err;
}

/**
 * @brief Send positive response
 */
void dcmdsd_send_positive_response(uint8_t sid, const uint8_t *data, uint16_t data_len, uint8_t address)
{
    uint8_t response[256];
    response[0] = sid + 0x40; // Positive response = SID + 0x40
    
    if (data != NULL && data_len > 0) {
        memcpy(&response[1], data, data_len);
    }
    
    dev_com_tp_sdu_t response_sdu;
    response_sdu.Address = address;
    response_sdu.SduBuffer = response;
    response_sdu.SduSize = 1 + data_len;
    dev_com_tp_transmit(&response_sdu);
}

/**
 * @brief Send negative response
 */
void dcmdsd_send_negative_response(uint8_t sid, uint8_t nrc, uint8_t address)
{
    uint8_t response[3];
    response[0] = 0x7F;  // Negative response SID
    response[1] = sid;   // Original service ID
    response[2] = nrc;   // Negative Response Code
    
    dev_com_tp_sdu_t response_sdu;
    response_sdu.Address = address;
    response_sdu.SduBuffer = response;
    response_sdu.SduSize = 3;
    dev_com_tp_transmit(&response_sdu);
}
