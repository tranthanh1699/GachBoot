#include "bl_uart_transport.h"
#include "platform_uart.h"

bl_status_t bl_uart_transport_init(bl_transport_t *transport)
{
    if (transport == (bl_transport_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    bl_transport_init(transport);
    return platform_uart_init();
}
