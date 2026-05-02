#ifndef BL_MEMORY_MAP_H
#define BL_MEMORY_MAP_H

#define BL_FLASH_BASE_ADDR               0x08000000u
#define BL_FLASH_SIZE                    0x00200000u
#define BL_RAM_DTCM_START_ADDR           0x20000000u
#define BL_RAM_DTCM_SIZE                 0x00020000u
#define BL_RAM_AXI_START_ADDR            0x24000000u
#define BL_RAM_AXI_SIZE                  0x00080000u
#define BL_RAM_SRAM123_START_ADDR        0x30000000u
#define BL_RAM_SRAM123_SIZE              0x00048000u
#define BL_RAM_SRAM4_START_ADDR          0x38000000u
#define BL_RAM_SRAM4_SIZE                0x00010000u

#define BL_BOOTLOADER_START_ADDR         0x08000000u
#define BL_BOOTLOADER_SIZE               0x00020000u

#define BL_APP_START_ADDR                0x08020000u
#define BL_APP_MAX_SIZE                  0x001C0000u
#define BL_APP_METADATA_ADDR             0x081FF000u

#define BL_APP_VALID_MARKER              0x47424C56u

#endif /* BL_MEMORY_MAP_H */
