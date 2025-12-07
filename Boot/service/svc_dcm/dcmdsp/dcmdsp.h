#ifndef DCMDSP_H
#define DCMDSP_H

#include "dev_common.h"
#include "svc_dcm.h"
#include "dcmdsl/dcmdsl.h"
#include "Service_PBCfg.h"
#include "DCM_Session_PBCfg.h"
/**
 * @brief Initialize DCMDSP layer
 */
Std_ReturnType dcmdsp_init(void);

/**
 * @brief Process UDS service request (unified interface via function pointer array)
 * @param service_id Service ID (SID)
 * @param message Request and response message structure
 * @param error_code NRC if error (output)
 * @return Std_ReturnType E_OK (handler found and success), E_NOT_OK (handler found but error), DCM_E_PENDING (handler pending)
 */
Std_ReturnType dcmdsp_process_service(uint8_t service_id, const uds_message_t *message, ErrorCode_t *error_code);

/**
 * @brief Build negative response
 * @param sid Service ID
 * @param nrc Negative Response Code
 * @param buffer Response buffer
 * @param buffer_len Response buffer length (output)
 */
void dcmdsp_build_negative_response(uint8_t sid, uint8_t nrc, uint8_t *buffer, uint16_t *buffer_len);

/**
 * @brief Check session and security for service
 * @param service_id Service ID (SID)
 * @param error_code NRC if error (output)
 * @return Std_ReturnType E_OK if allowed, E_NOT_OK if denied
 */
extern Std_ReturnType dcmdsp_check_session_security(uint8_t service_id, ErrorCode_t *error_code);

#endif // DCMDSP_H
