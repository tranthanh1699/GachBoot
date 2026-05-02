#include "platform_flash.h"
#include "bl_hw_config.h"
#include "bl_memory_map.h"
#include "stm32h7xx_hal.h"

bl_status_t platform_flash_erase_app_area(void)
{
    return BL_STATUS_NOT_SUPPORTED;
}

bl_status_t platform_flash_write(uint32_t address, const uint8_t *data, uint16_t length)
{
    (void)address;
    (void)data;
    (void)length;
    return BL_STATUS_NOT_SUPPORTED;
}

bl_status_t platform_flash_read(uint32_t address, uint8_t *data, uint16_t length)
{
    uint16_t index = 0u;
    const uint8_t *flash_ptr = (const uint8_t *)address;

    if ((data == (uint8_t *)0) || (length == 0u))
    {
        return BL_STATUS_PARAM;
    }

    for (index = 0u; index < length; index++)
    {
        data[index] = flash_ptr[index];
    }

    return BL_STATUS_OK;
}
