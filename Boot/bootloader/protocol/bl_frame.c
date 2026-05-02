#include "bl_frame.h"
#include "bl_checksum.h"

static void bl_write_u16_le(uint8_t *buffer, uint16_t value)
{
    buffer[0] = (uint8_t)(value & 0x00FFu);
    buffer[1] = (uint8_t)((value >> 8u) & 0x00FFu);
}

static uint16_t bl_read_u16_le(const uint8_t *buffer)
{
    return (uint16_t)((uint16_t)buffer[0] | ((uint16_t)buffer[1] << 8u));
}

bl_status_t bl_frame_encode(const bl_frame_t *frame, uint8_t *buffer, uint16_t buffer_size, uint16_t *encoded_size)
{
    uint16_t total_size = 0u;
    uint16_t crc_offset = 0u;
    uint16_t crc = 0u;
    uint16_t index = 0u;

    if ((frame == (const bl_frame_t *)0) || (buffer == (uint8_t *)0) || (encoded_size == (uint16_t *)0))
    {
        return BL_STATUS_PARAM;
    }

    if (frame->length > BL_FRAME_MAX_PAYLOAD_SIZE)
    {
        return BL_STATUS_PARAM;
    }

    total_size = (uint16_t)(BL_FRAME_HEADER_SIZE + frame->length + BL_FRAME_CHECKSUM_SIZE);
    if (buffer_size < total_size)
    {
        return BL_STATUS_PARAM;
    }

    buffer[0] = BL_FRAME_SOF;
    buffer[1] = frame->version;
    buffer[2] = frame->command;
    buffer[3] = frame->sequence;
    bl_write_u16_le(&buffer[4], frame->length);

    for (index = 0u; index < frame->length; index++)
    {
        buffer[BL_FRAME_HEADER_SIZE + index] = frame->payload[index];
    }

    crc_offset = (uint16_t)(BL_FRAME_HEADER_SIZE + frame->length);
    crc = bl_checksum_crc16_ccitt_false(&buffer[1], (uint16_t)(crc_offset - 1u));
    bl_write_u16_le(&buffer[crc_offset], crc);
    *encoded_size = total_size;

    return BL_STATUS_OK;
}

bl_status_t bl_frame_decode(const uint8_t *buffer, uint16_t buffer_size, bl_frame_t *frame, bl_error_t *error_code)
{
    uint16_t expected_size = 0u;
    uint16_t payload_length = 0u;
    uint16_t received_crc = 0u;
    uint16_t calculated_crc = 0u;
    uint16_t crc_offset = 0u;
    uint16_t index = 0u;

    if (error_code != (bl_error_t *)0)
    {
        *error_code = BL_ERROR_OK;
    }

    if ((buffer == (const uint8_t *)0) || (frame == (bl_frame_t *)0))
    {
        if (error_code != (bl_error_t *)0)
        {
            *error_code = BL_ERROR_INVALID_FRAME;
        }
        return BL_STATUS_PARAM;
    }

    if (buffer_size < (BL_FRAME_HEADER_SIZE + BL_FRAME_CHECKSUM_SIZE))
    {
        if (error_code != (bl_error_t *)0)
        {
            *error_code = BL_ERROR_INVALID_LENGTH;
        }
        return BL_STATUS_ERROR;
    }

    if (buffer[0] != BL_FRAME_SOF)
    {
        if (error_code != (bl_error_t *)0)
        {
            *error_code = BL_ERROR_INVALID_FRAME;
        }
        return BL_STATUS_ERROR;
    }

    payload_length = bl_read_u16_le(&buffer[4]);
    if (payload_length > BL_FRAME_MAX_PAYLOAD_SIZE)
    {
        if (error_code != (bl_error_t *)0)
        {
            *error_code = BL_ERROR_INVALID_LENGTH;
        }
        return BL_STATUS_ERROR;
    }

    expected_size = (uint16_t)(BL_FRAME_HEADER_SIZE + payload_length + BL_FRAME_CHECKSUM_SIZE);
    if (buffer_size != expected_size)
    {
        if (error_code != (bl_error_t *)0)
        {
            *error_code = BL_ERROR_INVALID_LENGTH;
        }
        return BL_STATUS_ERROR;
    }

    crc_offset = (uint16_t)(BL_FRAME_HEADER_SIZE + payload_length);
    received_crc = bl_read_u16_le(&buffer[crc_offset]);
    calculated_crc = bl_checksum_crc16_ccitt_false(&buffer[1], (uint16_t)(crc_offset - 1u));
    if (received_crc != calculated_crc)
    {
        if (error_code != (bl_error_t *)0)
        {
            *error_code = BL_ERROR_CHECKSUM_MISMATCH;
        }
        return BL_STATUS_CHECKSUM;
    }

    frame->version = buffer[1];
    frame->command = buffer[2];
    frame->sequence = buffer[3];
    frame->length = payload_length;
    for (index = 0u; index < payload_length; index++)
    {
        frame->payload[index] = buffer[BL_FRAME_HEADER_SIZE + index];
    }

    return BL_STATUS_OK;
}
