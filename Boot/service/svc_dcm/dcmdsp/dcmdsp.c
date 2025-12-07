#include "dcmdsp.h"


CONFIG_LOG_TAG(DCMDSP, true)

#define SERVICE_TABLE           dcm_service_config_table
#define SERVICE_TABLE_SIZE      DCM_SERVICE_COUNT 

extern uint8_t uds_security_get_active_level(void); 

/**
 * @brief Initialize DSP layer
 */
Std_ReturnType dcmdsp_init(void)
{
    DBG_OUT_I("DCMDSP Initialized");
    return E_OK;
}

static const dcm_service_config_t* get_service_config(uint8_t service_id)
{
    for (uint16_t i = 0; i < DCM_SERVICE_COUNT; i++) 
    {
        if (SERVICE_TABLE[i].service_id == service_id) {
            return &SERVICE_TABLE[i];
        }
    }
    return NULL;
}

Std_ReturnType dcmdsp_check_session_security(uint8_t service_id, ErrorCode_t *error_code)
{
    const dcm_service_config_t * service_config = get_service_config(service_id);
    if(service_config != NULL)
    {
        uint32_t session_mask = service_config->session_mask;
        uint32_t security_mask = service_config->security_mask;
        uint8_t current_session = dcmdsl_get_session();
        uint8_t current_security_level = uds_security_get_active_level();
    
        if(security_mask != 0)
        {
            if((session_mask & (uint32_t)(1 << current_session)) == 0)
            {
                *error_code = UDS_NRC_SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION; 
                return E_NOT_OK;
            }
        }

        if(security_mask != 0)
        {
            if((security_mask & (uint32_t)(1 << current_security_level)) == 0)
            {
                *error_code = UDS_NRC_SECURITY_ACCESS_DENIED; 
                return E_NOT_OK;
            }
        }
    }
    else
    {
        *error_code = UDS_NRC_SERVICE_NOT_SUPPORTED; 
        return E_NOT_OK;
    }

    *error_code = UDS_NRC_POSITIVE_RESPONSE; 
    return E_OK;
}

/**
 * @brief Process UDS service request (unified interface)
 */
Std_ReturnType dcmdsp_process_service(uint8_t service_id, const uds_message_t *message, ErrorCode_t *error_code)
{
    // Find service handler in table
    for (uint16_t i = 0; i < DCM_SERVICE_COUNT; i++) {
        if (SERVICE_TABLE[i].service_id == service_id) {
            Std_ReturnType result = E_NOT_OK;
            
            result = SERVICE_TABLE[i].handler(message, error_code);

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
