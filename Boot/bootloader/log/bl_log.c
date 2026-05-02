#include "bl_log.h"
#include "platform_uart.h"

#if (BL_ENABLE_LOG != 0u)
static uint16_t bl_log_strlen(const char *text)
{
    uint16_t length = 0u;

    if (text == (const char *)0)
    {
        return 0u;
    }

    while (text[length] != '\0')
    {
        length++;
    }

    return length;
}

static void bl_log_write(const char *prefix, const char *message)
{
    uint16_t prefix_length;
    uint16_t message_length;

    if (message == (const char *)0)
    {
        return;
    }

    prefix_length = bl_log_strlen(prefix);
    message_length = bl_log_strlen(message);

    (void)platform_uart_write((const uint8_t *)prefix, prefix_length);
    (void)platform_uart_write((const uint8_t *)message, message_length);
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
