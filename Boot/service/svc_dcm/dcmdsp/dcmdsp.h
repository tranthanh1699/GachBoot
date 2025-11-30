#ifndef DCMDSP_H
#define DCMDSP_H

#include "dev_common.h"
#include "svc_dcm.h"

/**
 * @brief UDS message structure (request + response)
 */
typedef struct {
    const uint8_t *request;     // Request buffer (including SID)
    uint16_t request_len;       // Request length
    uint8_t *response;          // Response buffer (output)
    uint16_t *response_len;     // Response length (output)
} uds_message_t;

/**
 * @brief Unified UDS service handler function pointer type
 * @param message Request and response buffers
 * @param error_code NRC if error (output) - separate parameter
 * @return Std_ReturnType E_OK (positive response), E_NOT_OK (negative response), DCM_E_PENDING (send 0x78)
 */
typedef Std_ReturnType (*uds_service_handler_t)(const uds_message_t *message, uint8_t *error_code);

/**
 * @brief Service handler table entry
 */
typedef struct {
    uint8_t service_id;
    uds_service_handler_t handler;
} uds_service_entry_t;

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
Std_ReturnType dcmdsp_process_service(uint8_t service_id, const uds_message_t *message, uint8_t *error_code);

/**
 * @brief Build negative response
 * @param sid Service ID
 * @param nrc Negative Response Code
 * @param buffer Response buffer
 * @param buffer_len Response buffer length (output)
 */
void dcmdsp_build_negative_response(uint8_t sid, uint8_t nrc, uint8_t *buffer, uint16_t *buffer_len);

#endif // DCMDSP_H
