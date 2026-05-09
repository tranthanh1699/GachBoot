#ifndef PLATFORM_FLASH_H
#define PLATFORM_FLASH_H

#include "bl_types.h"

bl_status_t platform_flash_erase_app_area(void);
bl_status_t platform_flash_invalidate_app_marker(void);
bl_status_t platform_flash_mark_app_valid(void);
bl_status_t platform_flash_write(uint32_t address, const uint8_t *data, uint16_t length);
bl_status_t platform_flash_read(uint32_t address, uint8_t *data, uint16_t length);

#endif /* PLATFORM_FLASH_H */
