#ifndef PLATFORM_BOOT_MODE_H
#define PLATFORM_BOOT_MODE_H

#include "bl_types.h"

bl_status_t platform_boot_mode_init(void);
bool platform_boot_mode_is_requested(void);

#endif /* PLATFORM_BOOT_MODE_H */
