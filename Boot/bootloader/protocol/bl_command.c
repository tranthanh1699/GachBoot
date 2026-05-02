#include "bl_command.h"
#include "bl_config.h"
#include "bl_memory.h"
#include "bl_memory_map.h"

static uint32_t bl_read_u32_le(const uint8_t *data)
{
    return ((uint32_t)data[0]) |
           ((uint32_t)data[1] << 8u) |
           ((uint32_t)data[2] << 16u) |
           ((uint32_t)data[3] << 24u);
}

static uint16_t bl_read_u16_le(const uint8_t *data)
{
    return (uint16_t)((uint16_t)data[0] | ((uint16_t)data[1] << 8u));
}

static void bl_write_u16_le(uint8_t *data, uint16_t value)
{
    data[0] = (uint8_t)(value & 0x00FFu);
    data[1] = (uint8_t)((value >> 8u) & 0x00FFu);
}

static void bl_write_u32_le(uint8_t *data, uint32_t value)
{
    data[0] = (uint8_t)(value & 0x000000FFu);
    data[1] = (uint8_t)((value >> 8u) & 0x000000FFu);
    data[2] = (uint8_t)((value >> 16u) & 0x000000FFu);
    data[3] = (uint8_t)((value >> 24u) & 0x000000FFu);
}

static uint32_t bl_get_capabilities(void)
{
    uint32_t capabilities = BL_CAP_CHECKSUM_CRC32 | BL_CAP_ABORT | BL_CAP_RESET;

#if (BL_ENABLE_SIGNATURE_VERIFY != 0u)
    capabilities |= BL_CAP_SIGNATURE_VERIFY;
#endif

    return capabilities;
}

void bl_command_build_error(uint8_t request_command, uint8_t sequence, bl_error_t error_code, bl_frame_t *response)
{
    if (response == (bl_frame_t *)0)
    {
        return;
    }

    response->version = BL_PROTOCOL_VERSION;
    response->command = BL_RSP_ERROR;
    response->sequence = sequence;
    response->length = 2u;
    response->payload[0] = request_command;
    response->payload[1] = (uint8_t)error_code;
}

static void bl_command_build_status_response(uint8_t command, uint8_t sequence, bl_error_t error_code, bl_frame_t *response)
{
    response->version = BL_PROTOCOL_VERSION;
    response->command = command;
    response->sequence = sequence;
    response->length = 1u;
    response->payload[0] = (uint8_t)error_code;
}

static bl_status_t bl_command_handle_hello(const bl_frame_t *request, bl_frame_t *response)
{
    uint32_t capabilities = bl_get_capabilities();

    if (request->length != 5u)
    {
        bl_command_build_error(request->command, request->sequence, BL_ERROR_INVALID_LENGTH, response);
        return BL_STATUS_ERROR;
    }

    if (request->payload[0] != BL_PROTOCOL_VERSION)
    {
        bl_command_build_error(request->command, request->sequence, BL_ERROR_UNSUPPORTED_VERSION, response);
        return BL_STATUS_ERROR;
    }

    response->version = BL_PROTOCOL_VERSION;
    response->command = BL_RSP_HELLO;
    response->sequence = request->sequence;
    response->length = 18u;
    response->payload[0] = BL_PROTOCOL_VERSION;
    response->payload[1] = BL_VERSION_MAJOR;
    response->payload[2] = BL_VERSION_MINOR;
    response->payload[3] = BL_VERSION_PATCH;
    bl_write_u32_le(&response->payload[4], capabilities);
    bl_write_u16_le(&response->payload[8], BL_FRAME_MAX_PAYLOAD_SIZE);
    bl_write_u32_le(&response->payload[10], BL_APP_START_ADDR);
    bl_write_u32_le(&response->payload[14], BL_APP_MAX_SIZE);

    return BL_STATUS_OK;
}

static bl_status_t bl_command_handle_download_start(bl_session_t *session, const bl_frame_t *request, bl_frame_t *response)
{
    uint32_t firmware_size;
    uint32_t firmware_crc32;
    uint32_t target_address;
    uint8_t signature_enabled;
    uint16_t signature_length;
    bl_status_t status;

    if (request->length < 15u)
    {
        bl_command_build_error(request->command, request->sequence, BL_ERROR_INVALID_LENGTH, response);
        return BL_STATUS_ERROR;
    }

    firmware_size = bl_read_u32_le(&request->payload[0]);
    firmware_crc32 = bl_read_u32_le(&request->payload[4]);
    target_address = bl_read_u32_le(&request->payload[8]);
    signature_enabled = request->payload[12];
    signature_length = bl_read_u16_le(&request->payload[13]);

    if (request->length != (uint16_t)(15u + signature_length))
    {
        bl_command_build_error(request->command, request->sequence, BL_ERROR_INVALID_LENGTH, response);
        return BL_STATUS_ERROR;
    }

    status = bl_session_set_metadata(session, firmware_size, firmware_crc32, target_address, signature_enabled,
                                     &request->payload[15], signature_length);
    if (status != BL_STATUS_OK)
    {
        if (status == BL_STATUS_NOT_SUPPORTED)
        {
            bl_command_build_error(request->command, request->sequence, BL_ERROR_FIRMWARE_SIGNATURE_INVALID, response);
        }
        else
        {
            bl_command_build_error(request->command, request->sequence, BL_ERROR_FIRMWARE_SIZE_INVALID, response);
        }
        return status;
    }

    bl_command_build_status_response(BL_RSP_DOWNLOAD_START, request->sequence, BL_ERROR_OK, response);
    return BL_STATUS_OK;
}

static bl_status_t bl_command_handle_data(bl_session_t *session, const bl_frame_t *request, bl_frame_t *response)
{
    uint32_t block_index;
    uint32_t target_offset;
    uint16_t data_length;
    uint32_t write_address;
    bl_status_t status;

    if (request->length < 10u)
    {
        bl_command_build_error(request->command, request->sequence, BL_ERROR_INVALID_LENGTH, response);
        return BL_STATUS_ERROR;
    }

    block_index = bl_read_u32_le(&request->payload[0]);
    target_offset = bl_read_u32_le(&request->payload[4]);
    data_length = bl_read_u16_le(&request->payload[8]);

    if (request->length != (uint16_t)(10u + data_length))
    {
        bl_command_build_error(request->command, request->sequence, BL_ERROR_INVALID_LENGTH, response);
        return BL_STATUS_ERROR;
    }

    status = bl_session_validate_block(session, block_index, target_offset, data_length);
    if (status != BL_STATUS_OK)
    {
        bl_command_build_error(request->command, request->sequence, BL_ERROR_INVALID_SEQUENCE, response);
        return status;
    }

    write_address = session->target_address + target_offset;
    status = bl_memory_write(write_address, &request->payload[10], data_length);
    if (status != BL_STATUS_OK)
    {
        bl_command_build_error(request->command, request->sequence, BL_ERROR_FLASH_WRITE_FAILED, response);
        return status;
    }

    status = bl_memory_verify(write_address, &request->payload[10], data_length);
    if (status != BL_STATUS_OK)
    {
        bl_command_build_error(request->command, request->sequence, BL_ERROR_FLASH_VERIFY_FAILED, response);
        return status;
    }

    status = bl_session_commit_block(session, data_length);
    if (status != BL_STATUS_OK)
    {
        bl_command_build_error(request->command, request->sequence, BL_ERROR_INTERNAL, response);
        return status;
    }

    response->version = BL_PROTOCOL_VERSION;
    response->command = BL_RSP_DATA;
    response->sequence = request->sequence;
    response->length = 5u;
    response->payload[0] = (uint8_t)BL_ERROR_OK;
    bl_write_u32_le(&response->payload[1], block_index);
    return BL_STATUS_OK;
}

bl_status_t bl_command_handle(bl_session_t *session, const bl_frame_t *request, bl_frame_t *response)
{
    bl_status_t status;

    if ((session == (bl_session_t *)0) || (request == (const bl_frame_t *)0) || (response == (bl_frame_t *)0))
    {
        return BL_STATUS_PARAM;
    }

    if (request->version != BL_PROTOCOL_VERSION)
    {
        bl_command_build_error(request->command, request->sequence, BL_ERROR_UNSUPPORTED_VERSION, response);
        return BL_STATUS_ERROR;
    }

    switch ((bl_command_id_t)request->command)
    {
        case BL_CMD_HELLO:
            status = bl_command_handle_hello(request, response);
            break;

        case BL_CMD_START_SESSION:
            status = bl_session_start(session);
            bl_command_build_status_response(BL_RSP_START_SESSION, request->sequence, BL_ERROR_OK, response);
            break;

        case BL_CMD_ERASE:
            if (session->state != BL_SESSION_STATE_ACTIVE)
            {
                bl_command_build_error(request->command, request->sequence, BL_ERROR_SESSION_NOT_ACTIVE, response);
                status = BL_STATUS_INVALID_STATE;
            }
            else if (bl_memory_erase_application() != BL_STATUS_OK)
            {
                bl_command_build_error(request->command, request->sequence, BL_ERROR_FLASH_ERASE_FAILED, response);
                status = BL_STATUS_IO;
            }
            else
            {
                bl_command_build_status_response(BL_RSP_ERASE, request->sequence, BL_ERROR_OK, response);
                status = BL_STATUS_OK;
            }
            break;

        case BL_CMD_DOWNLOAD_START:
            status = bl_command_handle_download_start(session, request, response);
            break;

        case BL_CMD_DATA:
            status = bl_command_handle_data(session, request, response);
            break;

        case BL_CMD_DOWNLOAD_END:
            status = bl_session_finalize(session);
            if (status != BL_STATUS_OK)
            {
                if (status == BL_STATUS_CHECKSUM)
                {
                    bl_command_build_error(request->command, request->sequence, BL_ERROR_FIRMWARE_CHECKSUM_INVALID, response);
                }
                else if (status == BL_STATUS_NOT_SUPPORTED)
                {
                    bl_command_build_error(request->command, request->sequence, BL_ERROR_FIRMWARE_SIGNATURE_INVALID, response);
                }
                else
                {
                    bl_command_build_error(request->command, request->sequence, BL_ERROR_INTERNAL, response);
                }
            }
            else
            {
                bl_command_build_status_response(BL_RSP_DOWNLOAD_END, request->sequence, BL_ERROR_OK, response);
            }
            break;

        case BL_CMD_RESET:
            bl_command_build_status_response(BL_RSP_RESET, request->sequence, BL_ERROR_OK, response);
            status = BL_STATUS_OK;
            break;

        case BL_CMD_ABORT:
            bl_session_abort(session);
            bl_command_build_status_response(BL_RSP_ABORT, request->sequence, BL_ERROR_OK, response);
            status = BL_STATUS_OK;
            break;

        default:
            bl_command_build_error(request->command, request->sequence, BL_ERROR_UNSUPPORTED_COMMAND, response);
            status = BL_STATUS_NOT_SUPPORTED;
            break;
    }

    return status;
}
