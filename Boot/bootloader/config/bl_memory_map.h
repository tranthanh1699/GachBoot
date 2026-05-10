#ifndef BL_MEMORY_MAP_H
#define BL_MEMORY_MAP_H

#include <stdint.h>


#define BL_FLASH_BASE_ADDR               0x08000000u        // Base address of the flash memory
#define BL_FLASH_SIZE                    0x00200000u        // Total size of the flash memory (2 MB)
#define BL_RAM_DTCM_START_ADDR           0x20000000u        // Start address of DTCM RAM
#define BL_RAM_DTCM_SIZE                 0x00020000u        // Size of DTCM RAM (128 KB)
#define BL_RAM_AXI_START_ADDR            0x24000000u
#define BL_RAM_AXI_SIZE                  0x00080000u        // Size of AXI RAM (512 KB)
#define BL_RAM_SRAM123_START_ADDR        0x30000000u        // Start address of SRAM1, SRAM2 and SRAM3
#define BL_RAM_SRAM123_SIZE              0x00048000u        // Size of SRAM1, SRAM2 and SRAM3 (288 KB)
#define BL_RAM_SRAM4_START_ADDR          0x38000000u        // Start address of SRAM4
#define BL_RAM_SRAM4_SIZE                0x00010000u        // Size of SRAM4 (64 KB)

#define BL_BOOTLOADER_START_ADDR         0x08000000u        // Start address of the bootloader located in bank 1
#define BL_BOOTLOADER_SIZE               0x00020000u        // Size of the bootloader (128 KB)

#define BL_APP_START_ADDR                0x08100000u        // Start address of the application located in bank 2
#define BL_APP_MAX_SIZE                  (128 * 1024u * 7)  // Maximum size of the application (7 banks of 128 KB each)
#define BL_APP_METADATA_ADDR             0x081E0000u        // Address of the application metadata located at the end of bank 7


#define BL_APP_VALID_MARKER              0x47424C56u

#define BL_APP_VALID_MARKER_SIZE         4u
#define BL_APP_METADATA_SIGNATURE_SIZE   256u

typedef struct {
    uint32_t crc;
    uint32_t app_size;
    uint32_t valid_marker;
    uint8_t signature[BL_APP_METADATA_SIGNATURE_SIZE];
} bl_app_metadata_t;


#endif /* BL_MEMORY_MAP_H */
