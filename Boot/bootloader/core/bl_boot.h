#ifndef BL_BOOT_H
#define BL_BOOT_H

#include "bl_types.h"

bl_status_t bl_boot_init(void);
bl_status_t bl_boot_jump_to_application_if_allowed(void);

#endif /* BL_BOOT_H */
