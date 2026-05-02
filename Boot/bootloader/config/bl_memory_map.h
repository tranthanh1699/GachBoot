#ifndef BL_MEMORY_MAP_H
#define BL_MEMORY_MAP_H

#define BL_FLASH_BASE_ADDR               0x08000000u
#define BL_FLASH_SIZE                    0x00200000u
#define BL_SRAM_BASE_ADDR                0x20000000u
#define BL_SRAM_SIZE                     0x00020000u

#define BL_BOOTLOADER_START_ADDR         0x08000000u
#define BL_BOOTLOADER_SIZE               0x00020000u

#define BL_APP_START_ADDR                0x08020000u
#define BL_APP_MAX_SIZE                  0x001C0000u
#define BL_APP_METADATA_ADDR             0x081FF000u

#define BL_APP_VALID_MARKER              0x47424C56u

#endif /* BL_MEMORY_MAP_H */
