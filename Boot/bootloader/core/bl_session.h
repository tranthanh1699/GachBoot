#ifndef BL_SESSION_H
#define BL_SESSION_H

#include "bl_security_config.h"
#include "bl_types.h"

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
    uint32_t firmware_size;
    uint32_t firmware_crc32;
    uint32_t target_address;
    uint32_t bytes_received;
    uint32_t expected_block_index;
    uint16_t signature_length;
    uint8_t signature_enabled;
    uint8_t signature[BL_SIGNATURE_MAX_SIZE];
    bl_session_state_t state;
} bl_session_t;

void bl_session_init(bl_session_t *session);
void bl_session_abort(bl_session_t *session);
bl_status_t bl_session_start(bl_session_t *session);
bl_status_t bl_session_set_metadata(bl_session_t *session, uint32_t firmware_size, uint32_t firmware_crc32,
                                    uint32_t target_address, uint8_t signature_enabled,
                                    const uint8_t *signature, uint16_t signature_length);
bl_status_t bl_session_validate_block(const bl_session_t *session, uint32_t block_index, uint32_t target_offset, uint16_t data_length);
bl_status_t bl_session_commit_block(bl_session_t *session, uint16_t data_length);

#endif /* BL_SESSION_H */
