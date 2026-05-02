#ifndef BL_COMMAND_H
#define BL_COMMAND_H

#include "bl_frame.h"
#include "bl_session.h"

bl_status_t bl_command_handle(bl_session_t *session, const bl_frame_t *request, bl_frame_t *response);
void bl_command_build_error(uint8_t request_command, uint8_t sequence, bl_error_t error_code, bl_frame_t *response);

#endif /* BL_COMMAND_H */
