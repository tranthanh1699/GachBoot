#ifndef UDS_SERVICE_0X11_H
#define UDS_SERVICE_0X11_H

#include "dev_common.h"
#include "dcmdsp/dcmdsp.h"

/**
 * @brief Service 0x11 handler - ECU Reset
 * @param message Request and response message structure
 * @param error_code NRC if error (output)
 * @return Std_ReturnType E_OK (positive response), E_NOT_OK (negative response), DCM_E_PENDING (pending)
 */
Std_ReturnType uds_service_0x11_handler(const uds_message_t *message, uint8_t *error_code);

/**
 * @brief Check if reset is pending and execute it
 * @note This function should be called periodically from main loop
 */
void uds_service_0x11_process_reset(void);

/**
 * @brief Get power down time for response (ISO 14229-1 requirement)
 * @return Power down time in milliseconds (0-255 range, scaled by 100ms)
 */
uint8_t uds_service_0x11_get_power_down_time(void);

#endif // UDS_SERVICE_0X11_H
