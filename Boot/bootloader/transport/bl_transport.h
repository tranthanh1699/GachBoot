#ifndef BL_TRANSPORT_H
#define BL_TRANSPORT_H

#include "bl_frame.h"

typedef struct
{
    uint8_t buffer[BL_FRAME_MAX_SIZE];
    uint16_t length;
    uint16_t expected_length;
    uint32_t last_rx_tick;
} bl_transport_t;

void bl_transport_init(bl_transport_t *transport);
bl_status_t bl_transport_poll_frame(bl_transport_t *transport, bl_frame_t *frame, bl_error_t *error_code);
bl_status_t bl_transport_send_frame(const bl_frame_t *frame);
void bl_transport_reset(bl_transport_t *transport);

#endif /* BL_TRANSPORT_H */
