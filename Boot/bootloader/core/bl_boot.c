#include "bl_boot.h"
#include "bl_app_jump.h"
#include "bl_app_validate.h"
#include "bl_memory_map.h"
#include "platform_boot_mode.h"

bl_status_t bl_boot_init(void)
{
    return platform_boot_mode_init();
}

bl_status_t bl_boot_jump_to_application_if_allowed(void)
{
    if (platform_boot_mode_is_requested() == true)
    {
        return BL_STATUS_BUSY;
    }

    if (bl_app_validate_application(BL_APP_START_ADDR) == false)
    {
        return BL_STATUS_INVALID_STATE;
    }

    return bl_app_jump_to_application(BL_APP_START_ADDR);
}
