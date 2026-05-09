#ifndef BL_MEMORY_H
#define BL_MEMORY_H

#include "bl_types.h"

bl_status_t bl_memory_erase_application(void);
bl_status_t bl_memory_invalidate_application_marker(void);
bl_status_t bl_memory_mark_application_valid(void);
bl_status_t bl_memory_write(uint32_t address, const uint8_t *data, uint16_t length);
bl_status_t bl_memory_verify(uint32_t address, const uint8_t *data, uint16_t length);

#endif /* BL_MEMORY_H */
