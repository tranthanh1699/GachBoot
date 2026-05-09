#include "bl_session.h"
#include "bl_config.h"
#include "bl_hw_config.h"
#include "bl_memory.h"
#include "bl_memory_map.h"
#include "bl_signature.h"

#define BL_CRC32_INIT_VALUE             0xFFFFFFFFu
#define BL_CRC32_POLY                   0xEDB88320u

static uint32_t bl_session_crc32_update_byte(uint32_t crc, uint8_t data)
{
    uint8_t bit_index = 0u;

    crc ^= (uint32_t)data;
    for (bit_index = 0u; bit_index < 8u; bit_index++)
    {
        if ((crc & 1u) != 0u)
        {
            crc = (crc >> 1u) ^ BL_CRC32_POLY;
        }
        else
        {
            crc >>= 1u;
        }
    }

    return crc;
}

static uint32_t bl_session_crc32_flash(uint32_t address, uint32_t length)
{
    uint32_t crc = BL_CRC32_INIT_VALUE;
    uint32_t index = 0u;
    const uint8_t *flash_data = (const uint8_t *)(uintptr_t)address;

    for (index = 0u; index < length; index++)
    {
        crc = bl_session_crc32_update_byte(crc, flash_data[index]);
    }

    return ~crc;
}

static bool bl_range_is_in_application(uint32_t address, uint32_t size)
{
    uint32_t app_end = 0u;
    uint32_t request_end = 0u;

    if (size == 0u)
    {
        return false;
    }

    app_end = BL_APP_START_ADDR + BL_APP_MAX_SIZE;
    request_end = address + size;
    if (request_end < address)
    {
        return false;
    }

    return ((address >= BL_APP_START_ADDR) && (request_end <= app_end));
}

static bool bl_size_align_up(uint32_t size, uint32_t alignment, uint32_t *aligned_size)
{
    uint32_t remainder;

    if ((size == 0u) || (alignment == 0u) || (aligned_size == (uint32_t *)0))
    {
        return false;
    }

    remainder = size % alignment;
    if (remainder == 0u)
    {
        *aligned_size = size;
    }
    else
    {
        uint32_t padding = alignment - remainder;
        *aligned_size = size + padding;
        if (*aligned_size < size)
        {
            return false;
        }
    }

    return true;
}

void bl_session_init(bl_session_t *session)
{
    uint16_t index = 0u;

    if (session == (bl_session_t *)0)
    {
        return;
    }

    session->firmware_size = 0u;
    session->firmware_crc32 = 0u;
    session->target_address = 0u;
    session->bytes_received = 0u;
    session->expected_block_index = 0u;
    session->signature_length = 0u;
    session->signature_enabled = 0u;
    session->state = BL_SESSION_STATE_READY;

    for (index = 0u; index < BL_SIGNATURE_MAX_SIZE; index++)
    {
        session->signature[index] = 0u;
    }
}

void bl_session_abort(bl_session_t *session)
{
    bl_session_init(session);
}

bl_status_t bl_session_start(bl_session_t *session)
{
    if (session == (bl_session_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    bl_session_init(session);
    session->state = BL_SESSION_STATE_ACTIVE;
    return BL_STATUS_OK;
}

bl_status_t bl_session_set_metadata(bl_session_t *session, uint32_t firmware_size, uint32_t firmware_crc32,
                                    uint32_t target_address, uint8_t signature_enabled,
                                    const uint8_t *signature, uint16_t signature_length)
{
    uint16_t index = 0u;
    uint32_t aligned_firmware_size = 0u;

    if (session == (bl_session_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    if (session->state != BL_SESSION_STATE_ACTIVE)
    {
        return BL_STATUS_INVALID_STATE;
    }

    if (bl_size_align_up(firmware_size, BL_PLATFORM_FLASH_WRITE_ALIGN, &aligned_firmware_size) == false)
    {
        return BL_STATUS_PARAM;
    }

    if (bl_range_is_in_application(target_address, aligned_firmware_size) == false)
    {
        return BL_STATUS_PARAM;
    }

    if (signature_length > BL_SIGNATURE_MAX_SIZE)
    {
        return BL_STATUS_PARAM;
    }

    if (bl_signature_is_required() == true)
    {
        if ((signature_enabled != 1u) || (signature_length != BL_SIGNATURE_MAX_SIZE))
        {
            return BL_STATUS_NOT_SUPPORTED;
        }
    }

    if ((signature_length > 0u) && (signature == (const uint8_t *)0))
    {
        return BL_STATUS_PARAM;
    }

    session->firmware_size = firmware_size;
    session->firmware_crc32 = firmware_crc32;
    session->target_address = target_address;
    session->bytes_received = 0u;
    session->expected_block_index = 0u;
    session->signature_enabled = signature_enabled;
    session->signature_length = signature_length;

    for (index = 0u; index < signature_length; index++)
    {
        session->signature[index] = signature[index];
    }

    session->state = BL_SESSION_STATE_DOWNLOAD;
    return BL_STATUS_OK;
}

bl_status_t bl_session_validate_block(const bl_session_t *session, uint32_t block_index, uint32_t target_offset, uint16_t data_length)
{
    uint32_t expected_offset = 0u;
    uint32_t next_total = 0u;

    if (session == (const bl_session_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    if (session->state != BL_SESSION_STATE_DOWNLOAD)
    {
        return BL_STATUS_INVALID_STATE;
    }

    if ((data_length == 0u) || (data_length > BL_FRAME_MAX_PAYLOAD_SIZE))
    {
        return BL_STATUS_PARAM;
    }

    if (block_index != session->expected_block_index)
    {
        return BL_STATUS_ERROR;
    }

    expected_offset = session->bytes_received;
    if (target_offset != expected_offset)
    {
        return BL_STATUS_ERROR;
    }

    if ((target_offset % BL_PLATFORM_FLASH_WRITE_ALIGN) != 0u)
    {
        return BL_STATUS_PARAM;
    }

    next_total = session->bytes_received + (uint32_t)data_length;
    if ((next_total < session->bytes_received) || (next_total > session->firmware_size))
    {
        return BL_STATUS_PARAM;
    }

    if ((next_total < session->firmware_size) && (((uint32_t)data_length % BL_PLATFORM_FLASH_WRITE_ALIGN) != 0u))
    {
        return BL_STATUS_PARAM;
    }

    return BL_STATUS_OK;
}

bl_status_t bl_session_commit_block(bl_session_t *session, uint16_t data_length)
{
    if (session == (bl_session_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    if (session->state != BL_SESSION_STATE_DOWNLOAD)
    {
        return BL_STATUS_INVALID_STATE;
    }

    session->bytes_received += (uint32_t)data_length;
    session->expected_block_index++;
    return BL_STATUS_OK;
}

bl_status_t bl_session_finalize(bl_session_t *session)
{
    uint32_t calculated_crc32;
    bl_status_t signature_status;

    if (session == (bl_session_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    if (session->state != BL_SESSION_STATE_DOWNLOAD)
    {
        return BL_STATUS_INVALID_STATE;
    }

    if (session->bytes_received != session->firmware_size)
    {
        return BL_STATUS_ERROR;
    }

    calculated_crc32 = bl_session_crc32_flash(session->target_address, session->firmware_size);
    if (calculated_crc32 != session->firmware_crc32)
    {
        return BL_STATUS_CHECKSUM;
    }

    if (bl_signature_is_required() == true)
    {
        signature_status = bl_signature_verify(session->target_address, session->firmware_size,
                                               session->signature, session->signature_length);
        if (signature_status != BL_STATUS_OK)
        {
            return signature_status;
        }
    }

    if (bl_memory_mark_application_valid() != BL_STATUS_OK)
    {
        return BL_STATUS_IO;
    }

    session->state = BL_SESSION_STATE_READY;
    return BL_STATUS_OK;
}
