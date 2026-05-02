#include "bl_main.h"
#include "bl_command.h"
#include "bl_protocol.h"
#include "bl_session.h"
#include "bl_transport.h"
#include "bl_uart_transport.h"
#include "platform_reset.h"

static bl_transport_t bl_main_transport;
static bl_session_t bl_main_session;

bl_status_t bl_main_init(void)
{
    bl_session_init(&bl_main_session);
    return bl_uart_transport_init(&bl_main_transport);
}

void bl_main_process(void)
{
    bl_frame_t request;
    bl_frame_t response;
    bl_error_t error_code = BL_ERROR_OK;
    bl_status_t status;

    status = bl_transport_poll_frame(&bl_main_transport, &request, &error_code);
    if (status == BL_STATUS_BUSY)
    {
        return;
    }

    if (status == BL_STATUS_TIMEOUT)
    {
        bl_session_abort(&bl_main_session);
        return;
    }

    if (status != BL_STATUS_OK)
    {
        bl_command_build_error(0u, 0u, error_code, &response);
        (void)bl_transport_send_frame(&response);
        return;
    }

    (void)bl_command_handle(&bl_main_session, &request, &response);
    (void)bl_transport_send_frame(&response);
    if ((request.command == BL_CMD_RESET) && (response.command == BL_RSP_RESET))
    {
        platform_reset_mcu();
    }
}
