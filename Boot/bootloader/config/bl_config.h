#ifndef BL_CONFIG_H
#define BL_CONFIG_H

#include <stdint.h>

#define BL_ENABLE_LOG                    0u
#define BL_LOG_BACKEND_UART              0u
#define BL_LOG_BACKEND_USB               0u

#ifndef BOOTLOADER_DEV
#define BOOTLOADER_DEV                   0u
#endif

#ifndef BOOTLOADER_RELEASE
#define BOOTLOADER_RELEASE               0u
#endif

#if ((BOOTLOADER_DEV != 0u) && (BOOTLOADER_RELEASE != 0u))
#error "Only one bootloader variant may be selected"
#endif

#if ((BOOTLOADER_DEV == 0u) && (BOOTLOADER_RELEASE == 0u))
#error "Select BOOTLOADER_DEV or BOOTLOADER_RELEASE"
#endif

#ifndef BL_ENABLE_SECURE_BOOT
#define BL_ENABLE_SECURE_BOOT            0u
#endif

#ifndef BL_ENABLE_SIGNATURE_VERIFY
#define BL_ENABLE_SIGNATURE_VERIFY       0u
#endif

#if ((BOOTLOADER_DEV != 0u) && (BL_ENABLE_SECURE_BOOT != 0u))
#error "Secure boot is only supported in Release builds"
#endif

#if ((BL_ENABLE_SECURE_BOOT != 0u) && (BOOTLOADER_RELEASE == 0u))
#error "Secure boot requires BOOTLOADER_RELEASE"
#endif

#if ((BL_ENABLE_SECURE_BOOT != 0u) && (BL_ENABLE_SIGNATURE_VERIFY == 0u))
#error "Secure boot requires signature verification"
#endif

#if ((BL_ENABLE_SIGNATURE_VERIFY != 0u) && ((BOOTLOADER_RELEASE == 0u) || (BL_ENABLE_SECURE_BOOT == 0u)))
#error "Signature verification requires Release build with secure boot enabled"
#endif

#define BL_ENABLE_CHECKSUM_VERIFY        1u

#define BL_PROTOCOL_VERSION              0x01u
#define BL_VERSION_MAJOR                 0u
#define BL_VERSION_MINOR                 1u
#define BL_VERSION_PATCH                 0u

#define BL_UART_BAUDRATE                 115200u
#define BL_UART_RX_BUFFER_SIZE           1024u
#define BL_COMM_TIMEOUT_MS               1000u
#define BL_FRAME_MAX_PAYLOAD_SIZE        490u
#define BL_FRAME_MAX_SIZE                (1u + 1u + 1u + 1u + 2u + BL_FRAME_MAX_PAYLOAD_SIZE + 2u)

#define BL_ENABLE_RETRY                  1u
#define BL_MAX_RETRY_COUNT               3u

#define BL_CAP_CHECKSUM_CRC32            0x00000001u
#define BL_CAP_SIGNATURE_VERIFY          0x00000002u
#define BL_CAP_ABORT                     0x00000004u
#define BL_CAP_RESET                     0x00000008u

#define BL_IS_APP_USE_CACHEABLE          0                   // Set to 1 if the application is allowed to use cacheable memory regions, 0 otherwise
#define BL_APP_NVIC_REGISTER_COUNT       8u

#endif /* BL_CONFIG_H */
