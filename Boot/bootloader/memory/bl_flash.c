#include "bl_flash.h"
#include "platform_flash.h"

bl_status_t bl_flash_erase_app_area(void)
{
    return platform_flash_erase_app_area();
}

bl_status_t bl_flash_invalidate_app_marker(void)
{
    return platform_flash_invalidate_app_marker();
}

bl_status_t bl_flash_mark_app_valid(void)
{
    return platform_flash_mark_app_valid();
}

bl_status_t bl_flash_write(uint32_t address, const uint8_t *data, uint16_t length)
{
    return platform_flash_write(address, data, length);
}

bl_status_t bl_flash_read(uint32_t address, uint8_t *data, uint16_t length)
{
    return platform_flash_read(address, data, length);
}
