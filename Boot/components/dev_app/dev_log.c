#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include "dev_log.h"
#include "usbd_cdc_if.h"

/**
 * @brief This function to log message
 * @param str The format string
 * @param ... The variable arguments
 */
void dev_log(const char* str, ...)
{

    char log_buffer[256];
    va_list args;
    va_start(args, str);
    vsnprintf(log_buffer, sizeof(log_buffer), str, args);
    va_end(args);
    CDC_Transmit_FS((uint8_t *)log_buffer, strlen(log_buffer));
}