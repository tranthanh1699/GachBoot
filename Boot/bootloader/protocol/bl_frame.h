#ifndef BL_FRAME_H
#define BL_FRAME_H

#include "bl_config.h"
#include "bl_protocol.h"
#include "bl_types.h"

typedef struct
{
    uint8_t version;
    uint8_t command;
    uint8_t sequence;
    uint16_t length;
    uint8_t payload[BL_FRAME_MAX_PAYLOAD_SIZE];
} bl_frame_t;

bl_status_t bl_frame_encode(const bl_frame_t *frame, uint8_t *buffer, uint16_t buffer_size, uint16_t *encoded_size);
bl_status_t bl_frame_decode(const uint8_t *buffer, uint16_t buffer_size, bl_frame_t *frame, bl_error_t *error_code);

#endif /* BL_FRAME_H */
