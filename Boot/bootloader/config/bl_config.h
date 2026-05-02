#ifndef BL_CONFIG_H
#define BL_CONFIG_H

#include <stdint.h>

#define BL_ENABLE_LOG                    0u
#define BL_LOG_BACKEND_UART              0u
#define BL_LOG_BACKEND_USB               0u

#define BL_ENABLE_SIGNATURE_VERIFY       0u
#define BL_ENABLE_CHECKSUM_VERIFY        1u

#define BL_PROTOCOL_VERSION              0x01u
#define BL_VERSION_MAJOR                 0u
#define BL_VERSION_MINOR                 1u
#define BL_VERSION_PATCH                 0u

#define BL_UART_BAUDRATE                 115200u
#define BL_COMM_TIMEOUT_MS               1000u
#define BL_FRAME_MAX_PAYLOAD_SIZE        490u
#define BL_FRAME_MAX_SIZE                (1u + 1u + 1u + 1u + 2u + BL_FRAME_MAX_PAYLOAD_SIZE + 2u)

#define BL_ENABLE_RETRY                  1u
#define BL_MAX_RETRY_COUNT               3u

#define BL_CAP_CHECKSUM_CRC32            0x00000001u
#define BL_CAP_SIGNATURE_VERIFY          0x00000002u
#define BL_CAP_ABORT                     0x00000004u
#define BL_CAP_RESET                     0x00000008u

#endif /* BL_CONFIG_H */
