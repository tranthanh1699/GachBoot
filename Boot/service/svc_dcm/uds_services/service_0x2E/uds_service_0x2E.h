#ifndef UDS_SERVICE_0X2E_H
#define UDS_SERVICE_0X2E_H

#include "dev_common.h"
#include "dcmdsp/dcmdsp.h"

/**
 * @brief Service 0x2E handler - Write Data By Identifier
 * @param message Request and response message structure
 * @param error_code NRC if error (output)
 * @return Std_ReturnType E_OK (positive response), E_NOT_OK (negative response), DCM_E_PENDING (pending)
 */
Std_ReturnType uds_service_0x2e_handler(const uds_message_t *message, uint8_t *error_code);

#endif // UDS_SERVICE_0X2E_H
