#ifndef BL_SESSION_H
#define BL_SESSION_H

#include "bl_security_config.h"
#include "bl_types.h"
#include "bl_signature.h"

typedef enum
{
    BL_SESSION_STATE_IDLE = 0,
    BL_SESSION_STATE_READY,
    BL_SESSION_STATE_ACTIVE,
    BL_SESSION_STATE_DOWNLOAD,
    BL_SESSION_STATE_ERROR
} bl_session_state_t;

typedef struct
{
    uint32_t package_size;
    uint32_t package_crc32;
    uint32_t app_size;
    uint32_t app_crc32;
    uint32_t target_address;
    uint32_t bytes_received;
    uint32_t app_bytes_received;
    uint32_t app_bytes_written;
    uint32_t expected_package_size;
    uint32_t signature_crc32;
    uint32_t expected_block_index;
    uint16_t package_header_received;
    uint16_t signature_header_received;
    uint16_t write_buffer_length;
    uint16_t signature_length;
    uint8_t signature_enabled;
    uint8_t package_header[10];
    uint8_t signature_header[10];
    uint8_t write_buffer[32];
    uint8_t signature[BL_SIGNATURE_MAX_SIZE];
    bool app_header_valid;
    bool signature_header_valid;
    bl_session_state_t state;
    bl_sha256_ctx_t sha256_ctx;
} bl_session_t;

void bl_session_init(bl_session_t *session);
void bl_session_abort(bl_session_t *session);
bl_status_t bl_session_start(bl_session_t *session);
bl_status_t bl_session_set_metadata(bl_session_t *session, uint32_t package_size, uint32_t package_crc32,
                                    uint32_t target_address, uint8_t signature_enabled,
                                    const uint8_t *signature, uint16_t signature_length);
bl_status_t bl_session_validate_block(const bl_session_t *session, uint32_t block_index, uint32_t target_offset, uint16_t data_length);
bl_status_t bl_session_commit_block(bl_session_t *session, uint16_t data_length);
bl_status_t bl_session_process_block(bl_session_t *session, uint32_t block_index, uint32_t target_offset,
                                     const uint8_t *data, uint16_t data_length);
bl_status_t bl_session_finalize(bl_session_t *session);

#endif /* BL_SESSION_H */
