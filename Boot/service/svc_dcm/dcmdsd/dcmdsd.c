#include "dcmdsd.h"
#include "svc_dcm.h"
#include "dcmdsp/dcmdsp.h"
#include <string.h>

CONFIG_LOG_TAG(DCMDSD, true)

/**
 * @brief Initialize DSD layer
 */
dev_err_t dcmdsd_init(void)
{
    DBG_OUT_I("DCMDSD Initialized");
    return DEV_OK;
}

/**
 * @brief Process diagnostic request - dispatch to appropriate service
 */
dev_err_t dcmdsd_process_request(dev_com_tp_sdu_t * sdu_info_p)
{
    DEV_RETURN_ON_FALSE(sdu_info_p != NULL, DEV_ERR_INVALID_ARG, "SDU Info pointer is NULL");
    DEV_RETURN_ON_FALSE(sdu_info_p->SduBuffer != NULL, DEV_ERR_INVALID_ARG, "SDU Buffer is NULL");
    DEV_RETURN_ON_FALSE(sdu_info_p->SduSize > 0, DEV_ERR_INVALID_ARG, "SDU Size is zero");
    
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
        // Service is pending - NRC 0x78 already built by DCMDSP
        DBG_OUT_I("Service 0x%02X pending - sending NRC 0x78", sid);
        // Send NRC 0x78 (Response Pending)
        dev_com_tp_sdu_t response_sdu;
        response_sdu.Address = sdu_info_p->Address;
        response_sdu.SduBuffer = response_buffer;
        response_sdu.SduSize = response_len;
        dev_com_tp_transmit(&response_sdu);
        // Keep state for next cycle
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
