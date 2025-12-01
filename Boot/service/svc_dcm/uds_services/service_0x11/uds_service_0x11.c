#include "uds_service_0x11.h"
#include "svc_dcm.h"
#include "dcmdsl/dcmdsl.h"
#include "../service_0x27/uds_security_config.h"

CONFIG_LOG_TAG(UDS_0x11, true)

// Reset sub-functions (ISO 14229-1)
#define UDS_RESET_HARD_RESET                    0x01
#define UDS_RESET_KEY_OFF_ON_RESET              0x02
#define UDS_RESET_SOFT_RESET                    0x03
#define UDS_RESET_ENABLE_RAPID_POWER_SHUTDOWN   0x04
#define UDS_RESET_DISABLE_RAPID_POWER_SHUTDOWN  0x05

// Power down time in milliseconds (time before actual reset)
#define UDS_RESET_POWER_DOWN_TIME_MS            1000u

// Reset flag for main loop to execute reset
static volatile bool reset_pending = false;
static volatile uint8_t reset_type = 0;
static volatile uint32_t reset_time_ms = 0;

/**
 * @brief Service 0x11 handler - ECU Reset
 */
Std_ReturnType uds_service_0x11_handler(const uds_message_t *message, uint8_t *error_code)
{
    // Phase 1: Validate request length (SID + SubFunction)
    if (message->request_len != 2) {
        DBG_OUT_E("Invalid message length: %d (expected 2)", message->request_len);
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }

    // Phase 2: Extract sub-function
    uint8_t sub_function = message->request[1];
    
    DBG_OUT_I("ECU Reset: SubFunction=0x%02X", sub_function);

    // Phase 3: Validate sub-function
    if (sub_function != UDS_RESET_HARD_RESET &&
        sub_function != UDS_RESET_KEY_OFF_ON_RESET &&
        sub_function != UDS_RESET_SOFT_RESET &&
        sub_function != UDS_RESET_ENABLE_RAPID_POWER_SHUTDOWN &&
        sub_function != UDS_RESET_DISABLE_RAPID_POWER_SHUTDOWN) {
        DBG_OUT_E("Invalid sub-function: 0x%02X", sub_function);
        *error_code = UDS_NRC_SUBFUNCTION_NOT_SUPPORTED;
        return E_NOT_OK;
    }

    // Phase 4: Check session support (reset requires Programming or Extended session)
    uint8_t current_session = dcmdsl_get_active_session();
    
    if (current_session == UDS_SESSION_DEFAULT) {
        DBG_OUT_E("Reset not allowed in Default session");
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }

    // Phase 5: Check security for hard reset (Programming session requires security)
    if (sub_function == UDS_RESET_HARD_RESET && current_session == UDS_SESSION_PROGRAMMING) {
        uint8_t current_level = uds_security_get_active_level();
        
        if (current_level == UDS_SECURITY_LEVEL_LOCKED) {
            DBG_OUT_E("Hard reset requires security access in Programming session");
            *error_code = UDS_NRC_SECURITY_ACCESS_DENIED;
            return E_NOT_OK;
        }
    }

    // Phase 6: Build positive response (SubFunction only)
    message->response[0] = sub_function;
    *(message->response_len) = 1;

    // Phase 7: Schedule reset (will execute after response is sent)
    reset_pending = true;
    reset_type = sub_function;
    reset_time_ms = DEV_GET_TICK_MS() + UDS_RESET_POWER_DOWN_TIME_MS;

    DBG_OUT_I("ECU Reset scheduled: Type=0x%02X, Time=%u ms", reset_type, UDS_RESET_POWER_DOWN_TIME_MS);

    return E_OK;
}

/**
 * @brief Check if reset is pending and execute it
 * @note This function should be called periodically from main loop
 */
void uds_service_0x11_process_reset(void)
{
    if (!reset_pending) {
        return;
    }

    // Check if power down time has elapsed
    if (DEV_GET_TICK_MS() >= reset_time_ms) {
        DBG_OUT_I("Executing ECU Reset: Type=0x%02X", reset_type);

        // Perform reset based on type
        switch (reset_type) {
            case UDS_RESET_HARD_RESET:
            case UDS_RESET_KEY_OFF_ON_RESET:
            case UDS_RESET_SOFT_RESET:
                // Trigger system reset
                DBG_OUT_I("Performing system reset...");
                // Add delay to ensure log is flushed
                for (volatile uint32_t i = 0; i < 100000; i++);
                NVIC_SystemReset();
                break;

            case UDS_RESET_ENABLE_RAPID_POWER_SHUTDOWN:
                DBG_OUT_I("Rapid power shutdown enabled");
                // TODO: Implement rapid power shutdown enable
                reset_pending = false;
                break;

            case UDS_RESET_DISABLE_RAPID_POWER_SHUTDOWN:
                DBG_OUT_I("Rapid power shutdown disabled");
                // TODO: Implement rapid power shutdown disable
                reset_pending = false;
                break;

            default:
                DBG_OUT_E("Unknown reset type: 0x%02X", reset_type);
                reset_pending = false;
                break;
        }
    }
}

/**
 * @brief Get power down time for response (ISO 14229-1 requirement)
 * @return Power down time in milliseconds (0-255 range, scaled by 100ms)
 */
uint8_t uds_service_0x11_get_power_down_time(void)
{
    // Convert milliseconds to 100ms units (0-255 range)
    // 1000ms = 10 * 100ms = 0x0A
    return (uint8_t)(UDS_RESET_POWER_DOWN_TIME_MS / 100);
}
