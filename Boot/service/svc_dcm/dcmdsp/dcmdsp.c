#include "dcmdsp.h"
#include "svc_dcm.h"
#include "uds_services/service_0x10/uds_service_0x10.h"
#include "uds_services/service_0x3E/uds_service_0x3E.h"
#include "uds_services/service_0x22/uds_service_0x22.h"
#include "uds_services/service_0x2E/uds_service_0x2E.h"
#include "uds_services/service_0x27/uds_service_0x27.h"
#include "uds_services/service_0x31/uds_service_0x31.h"

CONFIG_LOG_TAG(DCMDSP, true)

// Service handler table
static const uds_service_entry_t service_table[] = {
    {UDS_SID_DIAGNOSTIC_SESSION_CONTROL, uds_service_0x10_handler},
    {UDS_SID_READ_DATA_BY_ID, uds_service_0x22_handler},
    {UDS_SID_SECURITY_ACCESS, uds_service_0x27_handler},
    {UDS_SID_WRITE_DATA_BY_ID, uds_service_0x2e_handler},
    {UDS_SID_ROUTINE_CONTROL, uds_service_0x31_handler},
    {UDS_SID_TESTER_PRESENT, uds_service_0x3e_handler},
};

#define SERVICE_TABLE_SIZE (sizeof(service_table) / sizeof(uds_service_entry_t))

/**
 * @brief Initialize DSP layer
 */
Std_ReturnType dcmdsp_init(void)
{
    DBG_OUT_I("DCMDSP Initialized");
    return E_OK;
}

/**
 * @brief Process UDS service request (unified interface)
 */
Std_ReturnType dcmdsp_process_service(uint8_t service_id, const uds_message_t *message, uint8_t *error_code)
{
    // Find service handler in table
    for (uint16_t i = 0; i < SERVICE_TABLE_SIZE; i++) {
        if (service_table[i].service_id == service_id) {
            // Call service handler
            Std_ReturnType result = service_table[i].handler(message, error_code);

            // Check result
            if (result == DCM_E_PENDING) {
                // Service is pending - send NRC 0x78 (Response Pending)
                *error_code = UDS_NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING;
                dcmdsp_build_negative_response(service_id, *error_code, message->response, message->response_len);
                return DCM_E_PENDING;
            }
            else if (result == E_NOT_OK) {
                // Build negative response
                dcmdsp_build_negative_response(service_id, *error_code, message->response, message->response_len);
                return E_NOT_OK;
            }
            
            // E_OK - Build positive response
            // Service handler filled response data, now add positive response SID
            if (*(message->response_len) > 0) {
                // Shift data right by 1 byte to make room for positive SID
                for (int16_t i = *(message->response_len) - 1; i >= 0; i--) {
                    message->response[i + 1] = message->response[i];
                }
                // Add positive response SID (request SID + 0x40)
                message->response[0] = service_id + 0x40;
                *(message->response_len) += 1;
            }
            // If E_OK with length=0, suppress response (e.g., Service 0x3E with bit 7 set)

            return E_OK;
        }
    }

    // Service not found in table
    return E_NOT_OK;
}

/**
 * @brief Build negative response
 */
void dcmdsp_build_negative_response(uint8_t sid, uint8_t nrc, uint8_t *buffer, uint16_t *buffer_len)
{
    buffer[0] = 0x7F;  // Negative response SID
    buffer[1] = sid;   // Original service ID
    buffer[2] = nrc;   // Negative Response Code
    *buffer_len = 3;
}
