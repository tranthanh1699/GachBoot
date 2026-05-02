#ifndef BL_FLASH_H
#define BL_FLASH_H

#include "bl_types.h"

bl_status_t bl_flash_erase_app_area(void);
bl_status_t bl_flash_write(uint32_t address, const uint8_t *data, uint16_t length);
bl_status_t bl_flash_read(uint32_t address, uint8_t *data, uint16_t length);

#endif /* BL_FLASH_H */
