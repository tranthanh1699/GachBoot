#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include "dev_log.h"
#include "usbd_cdc_if.h"
#include "main.h"  // For HAL_Delay

/**
 * @brief This function to log message
 * @param str The format string
 * @param ... The variable arguments
 */
void dev_log(const char* str, ...)
{
    if (!CDC_IsReady()) {
        return;
    }

    char log_buffer[512];
    va_list args;
    va_start(args, str);
    vsnprintf(log_buffer, sizeof(log_buffer), str, args);
    va_end(args);
    
    // Retry up to 100 times with small delay if USB is busy
    uint16_t len = strlen(log_buffer);
    for (int retry = 0; retry < 100; retry++) {
        uint8_t result = CDC_Transmit_FS((uint8_t *)log_buffer, len);
        if (result == USBD_OK) {
            break;  // Success
        }
        // USB busy, wait a bit
        HAL_Delay(1);
    }
}

void dev_log_hex(const uint8_t* data, uint32_t length)
{
    if (!CDC_IsReady()) {
        return;
    }

    char hex_buf[1024];
    int hex_idx = 0;
    dev_log("Hex Dump - Length: %d\r\n", length);
    
    // Add small delay to ensure previous log is sent
    HAL_Delay(5);
    
    for (uint32_t i = 0; i < length; i++) {
        if (i % 16 == 0 && hex_idx > 0) {
            hex_buf[hex_idx] = '\0';
            dev_log("%s\r\n", hex_buf);
            HAL_Delay(2);  // Small delay between lines
            hex_idx = 0;
        }
        if (i % 16 == 0) {
            hex_idx += snprintf(&hex_buf[hex_idx], sizeof(hex_buf) - hex_idx, "     ");
        }
        hex_idx += snprintf(&hex_buf[hex_idx], sizeof(hex_buf) - hex_idx, "%02X ", data[i]);
    }
    if (hex_idx > 0) {
        hex_buf[hex_idx] = '\0';
        dev_log("%s\r\n", hex_buf);
    }
}
