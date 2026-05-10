#include "bl_session.h"
#include "bl_config.h"
#include "bl_hw_config.h"
#include "bl_memory.h"
#include "bl_memory_map.h"
#include "bl_signature.h"

#define BL_CRC32_INIT_VALUE             0xFFFFFFFFu
#define BL_CRC32_POLY                   0xEDB88320u
#define BL_PACKAGE_APP_SECTION_ID        0xA501u
#define BL_PACKAGE_SIGNATURE_SECTION_ID  0x5A02u
#define BL_PACKAGE_SECTION_HEADER_SIZE   10u
#define BL_PACKAGE_SIGNATURE_SIZE        256u

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

static uint32_t bl_session_crc32_buffer(const uint8_t *data, uint32_t length)
{
    uint32_t crc = BL_CRC32_INIT_VALUE;
    uint32_t index = 0u;

    for (index = 0u; index < length; index++)
    {
        crc = bl_session_crc32_update_byte(crc, data[index]);
    }

    return ~crc;
}

static uint16_t bl_session_read_u16_le(const uint8_t *data)
{
    return (uint16_t)((uint16_t)data[0] | ((uint16_t)data[1] << 8u));
}

static uint32_t bl_session_read_u32_le(const uint8_t *data)
{
    return ((uint32_t)data[0]) |
           ((uint32_t)data[1] << 8u) |
           ((uint32_t)data[2] << 16u) |
           ((uint32_t)data[3] << 24u);
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

    session->package_size = 0u;
    session->package_crc32 = 0u;
    session->app_size = 0u;
    session->app_crc32 = 0u;
    session->target_address = 0u;
    session->bytes_received = 0u;
    session->app_bytes_received = 0u;
    session->app_bytes_written = 0u;
    session->expected_package_size = 0u;
    session->signature_crc32 = 0u;
    session->expected_block_index = 0u;
    session->package_header_received = 0u;
    session->signature_header_received = 0u;
    session->write_buffer_length = 0u;
    session->signature_length = 0u;
    session->signature_enabled = 0u;
    session->app_header_valid = false;
    session->signature_header_valid = false;
    session->state = BL_SESSION_STATE_READY;

    for (index = 0u; index < BL_SIGNATURE_MAX_SIZE; index++)
    {
        session->signature[index] = 0u;
    }

    for (index = 0u; index < BL_PACKAGE_SECTION_HEADER_SIZE; index++)
    {
        session->package_header[index] = 0u;
        session->signature_header[index] = 0u;
    }

    for (index = 0u; index < BL_PLATFORM_FLASH_WRITE_ALIGN; index++)
    {
        session->write_buffer[index] = 0u;
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

bl_status_t bl_session_set_metadata(bl_session_t *session, uint32_t package_size, uint32_t package_crc32,
                                    uint32_t target_address, uint8_t signature_enabled,
                                    const uint8_t *signature, uint16_t signature_length)
{
    uint16_t index = 0u;

    if (session == (bl_session_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    if (session->state != BL_SESSION_STATE_ACTIVE)
    {
        return BL_STATUS_INVALID_STATE;
    }

    if (package_size < ((2u * BL_PACKAGE_SECTION_HEADER_SIZE) + BL_PACKAGE_SIGNATURE_SIZE))
    {
        return BL_STATUS_PARAM;
    }

    if (bl_range_is_in_application(target_address, BL_PLATFORM_FLASH_WRITE_ALIGN) == false)
    {
        return BL_STATUS_PARAM;
    }

    if (signature_length > BL_SIGNATURE_MAX_SIZE)
    {
        return BL_STATUS_PARAM;
    }

    if (bl_signature_is_required() == true)
    {
        if (signature_enabled != 1u)
        {
            return BL_STATUS_NOT_SUPPORTED;
        }
    }

    if ((signature_length > 0u) && (signature == (const uint8_t *)0))
    {
        return BL_STATUS_PARAM;
    }

    session->package_size = package_size;
    session->package_crc32 = package_crc32;
    session->app_size = 0u;
    session->app_crc32 = 0u;
    session->target_address = target_address;
    session->bytes_received = 0u;
    session->app_bytes_received = 0u;
    session->app_bytes_written = 0u;
    session->expected_package_size = 0u;
    session->signature_crc32 = 0u;
    session->expected_block_index = 0u;
    session->package_header_received = 0u;
    session->signature_header_received = 0u;
    session->write_buffer_length = 0u;
    session->signature_enabled = signature_enabled;
    session->signature_length = 0u;
    session->app_header_valid = false;
    session->signature_header_valid = false;

    for (index = 0u; index < BL_SIGNATURE_MAX_SIZE; index++)
    {
        session->signature[index] = 0u;
    }

    (void)signature;
    (void)signature_length;

    bl_sha256_init(&session->sha256_ctx);
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

    next_total = session->bytes_received + (uint32_t)data_length;
    if ((next_total < session->bytes_received) || (next_total > session->package_size))
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

static bl_status_t bl_session_flush_app_buffer(bl_session_t *session, bool final_flush)
{
    uint32_t write_address = 0u;
    bl_status_t status;

    if (session->write_buffer_length == 0u)
    {
        return BL_STATUS_OK;
    }

    if ((final_flush == false) && (session->write_buffer_length < BL_PLATFORM_FLASH_WRITE_ALIGN))
    {
        return BL_STATUS_OK;
    }

    if (session->signature_enabled) {
        bl_sha256_update(&session->sha256_ctx, session->write_buffer, session->write_buffer_length);
    }

    write_address = session->target_address + session->app_bytes_written;
    status = bl_memory_write(write_address, session->write_buffer, session->write_buffer_length);
    if (status != BL_STATUS_OK)
    {
        return status;
    }

    status = bl_memory_verify(write_address, session->write_buffer, session->write_buffer_length);
    if (status != BL_STATUS_OK)
    {
        return status;
    }

    session->app_bytes_written += (uint32_t)session->write_buffer_length;
    session->write_buffer_length = 0u;
    return BL_STATUS_OK;
}

static bl_status_t bl_session_parse_app_header(bl_session_t *session)
{
    uint16_t section_id = bl_session_read_u16_le(&session->package_header[0]);
    uint32_t aligned_app_size = 0u;

    if (section_id != BL_PACKAGE_APP_SECTION_ID)
    {
        return BL_STATUS_PARAM;
    }

    session->app_size = bl_session_read_u32_le(&session->package_header[2]);
    session->app_crc32 = bl_session_read_u32_le(&session->package_header[6]);

    if (bl_size_align_up(session->app_size, BL_PLATFORM_FLASH_WRITE_ALIGN, &aligned_app_size) == false)
    {
        return BL_STATUS_PARAM;
    }

    if (bl_range_is_in_application(session->target_address, aligned_app_size) == false)
    {
        return BL_STATUS_PARAM;
    }

    session->expected_package_size = BL_PACKAGE_SECTION_HEADER_SIZE +
                                     session->app_size +
                                     BL_PACKAGE_SECTION_HEADER_SIZE +
                                     BL_PACKAGE_SIGNATURE_SIZE;
    if (session->expected_package_size != session->package_size)
    {
        return BL_STATUS_PARAM;
    }

    session->app_header_valid = true;
    return BL_STATUS_OK;
}

static bl_status_t bl_session_parse_signature_header(bl_session_t *session)
{
    uint16_t section_id = bl_session_read_u16_le(&session->signature_header[0]);
    uint32_t signature_size = bl_session_read_u32_le(&session->signature_header[2]);

    if (section_id != BL_PACKAGE_SIGNATURE_SECTION_ID)
    {
        return BL_STATUS_PARAM;
    }

    if (signature_size != BL_PACKAGE_SIGNATURE_SIZE)
    {
        return BL_STATUS_PARAM;
    }

    session->signature_crc32 = bl_session_read_u32_le(&session->signature_header[6]);
    session->signature_header_valid = true;
    return BL_STATUS_OK;
}

static bl_status_t bl_session_store_app_byte(bl_session_t *session, uint8_t data)
{
    bl_status_t status;

    if (session->app_bytes_received >= session->app_size)
    {
        return BL_STATUS_PARAM;
    }

    session->write_buffer[session->write_buffer_length] = data;
    session->write_buffer_length++;
    session->app_bytes_received++;

    status = bl_session_flush_app_buffer(session, false);
    return status;
}

static bl_status_t bl_session_process_package_byte(bl_session_t *session, uint32_t package_offset, uint8_t data)
{
    bl_status_t status;
    uint32_t signature_start = 0u;
    uint32_t signature_index = 0u;

    if (session->package_header_received < BL_PACKAGE_SECTION_HEADER_SIZE)
    {
        session->package_header[session->package_header_received] = data;
        session->package_header_received++;

        if (session->package_header_received == BL_PACKAGE_SECTION_HEADER_SIZE)
        {
            status = bl_session_parse_app_header(session);
            if (status != BL_STATUS_OK)
            {
                return status;
            }
        }

        return BL_STATUS_OK;
    }

    if (session->app_header_valid == false)
    {
        return BL_STATUS_INVALID_STATE;
    }

    if (session->app_bytes_received < session->app_size)
    {
        return bl_session_store_app_byte(session, data);
    }

    if (session->signature_header_received < BL_PACKAGE_SECTION_HEADER_SIZE)
    {
        session->signature_header[session->signature_header_received] = data;
        session->signature_header_received++;

        if (session->signature_header_received == BL_PACKAGE_SECTION_HEADER_SIZE)
        {
            status = bl_session_parse_signature_header(session);
            if (status != BL_STATUS_OK)
            {
                return status;
            }
        }

        return BL_STATUS_OK;
    }

    if (session->signature_header_valid == false)
    {
        return BL_STATUS_INVALID_STATE;
    }

    signature_start = BL_PACKAGE_SECTION_HEADER_SIZE + session->app_size + BL_PACKAGE_SECTION_HEADER_SIZE;
    signature_index = package_offset - signature_start;
    if (signature_index >= BL_PACKAGE_SIGNATURE_SIZE)
    {
        return BL_STATUS_PARAM;
    }

    session->signature[signature_index] = data;
    session->signature_length = (uint16_t)(signature_index + 1u);
    return BL_STATUS_OK;
}

bl_status_t bl_session_process_block(bl_session_t *session, uint32_t block_index, uint32_t target_offset,
                                     const uint8_t *data, uint16_t data_length)
{
    uint16_t index = 0u;
    bl_status_t status;

    if ((session == (bl_session_t *)0) || (data == (const uint8_t *)0))
    {
        return BL_STATUS_PARAM;
    }

    status = bl_session_validate_block(session, block_index, target_offset, data_length);
    if (status != BL_STATUS_OK)
    {
        return status;
    }

    for (index = 0u; index < data_length; index++)
    {
        status = bl_session_process_package_byte(session, target_offset + (uint32_t)index, data[index]);
        if (status != BL_STATUS_OK)
        {
            return status;
        }
    }

    status = bl_session_commit_block(session, data_length);
    return status;
}

bl_status_t bl_session_finalize(bl_session_t *session)
{
    uint8_t digest[BL_SHA256_DIGEST_SIZE];
    uint32_t calculated_crc32;
    uint32_t calculated_signature_crc32;
    bl_status_t signature_status;

    if (session == (bl_session_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    if (session->state != BL_SESSION_STATE_DOWNLOAD)
    {
        return BL_STATUS_INVALID_STATE;
    }

    if (session->bytes_received != session->package_size)
    {
        return BL_STATUS_ERROR;
    }

    if ((session->app_header_valid == false) || (session->signature_header_valid == false))
    {
        return BL_STATUS_ERROR;
    }

    if ((session->app_bytes_received != session->app_size) ||
        (session->signature_length != BL_PACKAGE_SIGNATURE_SIZE))
    {
        return BL_STATUS_ERROR;
    }

    signature_status = bl_session_flush_app_buffer(session, true);
    if (signature_status != BL_STATUS_OK)
    {
        return signature_status;
    }

    calculated_signature_crc32 = bl_session_crc32_buffer(session->signature, session->signature_length);
    if (calculated_signature_crc32 != session->signature_crc32)
    {
        return BL_STATUS_CHECKSUM;
    }

    calculated_crc32 = bl_session_crc32_flash(session->target_address, session->app_size);
    if (calculated_crc32 != session->app_crc32)
    {
        return BL_STATUS_CHECKSUM;
    }

    if (bl_signature_is_required() == true)
    {
        bl_sha256_final(&session->sha256_ctx, digest);
        signature_status = bl_signature_verify_digest(digest, session->signature, session->signature_length);
        if (signature_status != BL_STATUS_OK)
        {
            return signature_status;
        }
    }

    if (bl_memory_mark_application_valid(session->app_size, session->signature, session->signature_length) != BL_STATUS_OK)
    {
        return BL_STATUS_IO;
    }

    session->state = BL_SESSION_STATE_READY;
    return BL_STATUS_OK;
}
