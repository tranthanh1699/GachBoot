#ifndef UDS_SERVICE_0X36_H
#define UDS_SERVICE_0X36_H

#include "dev_common.h"
#include "dcmdsp/dcmdsp.h"

/**
 * @brief Service 0x36 handler - Transfer Data
 * @param message Request and response message structure
 * @param error_code NRC if error (output)
 * @return Std_ReturnType E_OK (positive response), E_NOT_OK (negative response), DCM_E_PENDING (pending)
 */
Std_ReturnType uds_service_0x36_handler(const uds_message_t *message, ErrorCode_t *error_code);

#endif // UDS_SERVICE_0X36_H