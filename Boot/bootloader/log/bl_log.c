#include "bl_log.h"
#include "platform_uart.h"

#if (BL_ENABLE_LOG != 0u)
static void bl_log_write(const char *prefix, const char *message)
{
    const char *cursor = message;
    uint16_t length = 0u;

    if (message == (const char *)0)
    {
        return;
    }

    while (cursor[length] != '\0')
    {
        length++;
    }

    (void)platform_uart_write((const uint8_t *)prefix, 5u);
    (void)platform_uart_write((const uint8_t *)message, length);
    (void)platform_uart_write((const uint8_t *)"\r\n", 2u);
}

void bl_log_info(const char *message)
{
    bl_log_write("I:BL ", message);
}

void bl_log_error(const char *message)
{
    bl_log_write("E:BL ", message);
}
#endif
