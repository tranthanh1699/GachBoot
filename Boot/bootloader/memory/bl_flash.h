#ifndef BL_FLASH_H
#define BL_FLASH_H

#include "bl_types.h"

bl_status_t bl_flash_erase_app_area(void);
bl_status_t bl_flash_invalidate_app_marker(void);
bl_status_t bl_flash_mark_app_valid(uint32_t app_size, const uint8_t *signature, uint16_t signature_length);
bl_status_t bl_flash_write(uint32_t address, const uint8_t *data, uint16_t length);
bl_status_t bl_flash_read(uint32_t address, uint8_t *data, uint16_t length);

#endif /* BL_FLASH_H */
