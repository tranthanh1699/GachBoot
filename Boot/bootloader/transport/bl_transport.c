#include "bl_transport.h"
#include "bl_config.h"
#include "platform_uart.h"

static uint16_t bl_transport_read_length(const uint8_t *buffer)
{
    return (uint16_t)((uint16_t)buffer[4] | ((uint16_t)buffer[5] << 8u));
}

void bl_transport_reset(bl_transport_t *transport)
{
    uint16_t index = 0u;

    if (transport == (bl_transport_t *)0)
    {
        return;
    }

    transport->length = 0u;
    transport->expected_length = 0u;
    transport->last_rx_tick = platform_uart_get_tick_ms();

    for (index = 0u; index < BL_FRAME_MAX_SIZE; index++)
    {
        transport->buffer[index] = 0u;
    }
}

void bl_transport_init(bl_transport_t *transport)
{
    bl_transport_reset(transport);
}

bl_status_t bl_transport_poll_frame(bl_transport_t *transport, bl_frame_t *frame, bl_error_t *error_code)
{
    uint8_t byte = 0u;
    bl_status_t status;
    uint32_t now_tick = 0u;

    if ((transport == (bl_transport_t *)0) || (frame == (bl_frame_t *)0))
    {
        return BL_STATUS_PARAM;
    }

    now_tick = platform_uart_get_tick_ms();
    if ((transport->length > 0u) && ((now_tick - transport->last_rx_tick) > BL_COMM_TIMEOUT_MS))
    {
        bl_transport_reset(transport);
        if (error_code != (bl_error_t *)0)
        {
            *error_code = BL_ERROR_TIMEOUT;
        }
        return BL_STATUS_TIMEOUT;
    }

    status = platform_uart_read_byte(&byte);
    if (status == BL_STATUS_TIMEOUT)
    {
        return BL_STATUS_BUSY;
    }

    if (status != BL_STATUS_OK)
    {
        return status;
    }

    transport->last_rx_tick = now_tick;

    if ((transport->length == 0u) && (byte != BL_FRAME_SOF))
    {
        return BL_STATUS_BUSY;
    }

    if (transport->length >= BL_FRAME_MAX_SIZE)
    {
        bl_transport_reset(transport);
        if (error_code != (bl_error_t *)0)
        {
            *error_code = BL_ERROR_INVALID_LENGTH;
        }
        return BL_STATUS_ERROR;
    }

    transport->buffer[transport->length] = byte;
    transport->length++;

    if (transport->length == BL_FRAME_HEADER_SIZE)
    {
        uint16_t payload_length = bl_transport_read_length(transport->buffer);
        if (payload_length > BL_FRAME_MAX_PAYLOAD_SIZE)
        {
            bl_transport_reset(transport);
            if (error_code != (bl_error_t *)0)
            {
                *error_code = BL_ERROR_INVALID_LENGTH;
            }
            return BL_STATUS_ERROR;
        }
        transport->expected_length = (uint16_t)(BL_FRAME_HEADER_SIZE + payload_length + BL_FRAME_CHECKSUM_SIZE);
    }

    if ((transport->expected_length > 0u) && (transport->length == transport->expected_length))
    {
        status = bl_frame_decode(transport->buffer, transport->length, frame, error_code);
        bl_transport_reset(transport);
        return status;
    }

    return BL_STATUS_BUSY;
}

bl_status_t bl_transport_send_frame(const bl_frame_t *frame)
{
    uint8_t buffer[BL_FRAME_MAX_SIZE];
    uint16_t encoded_size = 0u;
    bl_status_t status;

    status = bl_frame_encode(frame, buffer, BL_FRAME_MAX_SIZE, &encoded_size);
    if (status != BL_STATUS_OK)
    {
        return status;
    }

    return platform_uart_write(buffer, encoded_size);
}
