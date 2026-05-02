#ifndef BL_PROTOCOL_H
#define BL_PROTOCOL_H

#include "bl_types.h"

typedef enum
{
    BL_CMD_HELLO = 0x01u,
    BL_CMD_START_SESSION = 0x02u,
    BL_CMD_ERASE = 0x03u,
    BL_CMD_DOWNLOAD_START = 0x04u,
    BL_CMD_DATA = 0x05u,
    BL_CMD_DOWNLOAD_END = 0x06u,
    BL_CMD_RESET = 0x07u,
    BL_CMD_ABORT = 0x08u,

    BL_RSP_ERROR = 0x7Fu,
    BL_RSP_HELLO = 0x81u,
    BL_RSP_START_SESSION = 0x82u,
    BL_RSP_ERASE = 0x83u,
    BL_RSP_DOWNLOAD_START = 0x84u,
    BL_RSP_DATA = 0x85u,
    BL_RSP_DOWNLOAD_END = 0x86u,
    BL_RSP_RESET = 0x87u,
    BL_RSP_ABORT = 0x88u
} bl_command_id_t;

#define BL_FRAME_SOF                    0xA5u
#define BL_FRAME_HEADER_SIZE            6u
#define BL_FRAME_CHECKSUM_SIZE          2u

#endif /* BL_PROTOCOL_H */
