#include "bl_memory.h"
#include "bl_flash.h"
#include "bl_memory_map.h"

static bool bl_memory_range_is_valid(uint32_t address, uint16_t length)
{
    uint32_t end_address = 0u;
    uint32_t app_end = 0u;

    if (length == 0u)
    {
        return false;
    }

    end_address = address + (uint32_t)length;
    if (end_address < address)
    {
        return false;
    }

    app_end = BL_APP_START_ADDR + BL_APP_MAX_SIZE;
    return ((address >= BL_APP_START_ADDR) && (end_address <= app_end));
}

bl_status_t bl_memory_erase_application(void)
{
    return bl_flash_erase_app_area();
}

bl_status_t bl_memory_write(uint32_t address, const uint8_t *data, uint16_t length)
{
    if (data == (const uint8_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    if (bl_memory_range_is_valid(address, length) == false)
    {
        return BL_STATUS_PARAM;
    }

    return bl_flash_write(address, data, length);
}

bl_status_t bl_memory_verify(uint32_t address, const uint8_t *data, uint16_t length)
{
    uint8_t read_byte = 0u;
    uint16_t index = 0u;

    if (data == (const uint8_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    if (bl_memory_range_is_valid(address, length) == false)
    {
        return BL_STATUS_PARAM;
    }

    for (index = 0u; index < length; index++)
    {
        if (bl_flash_read(address + (uint32_t)index, &read_byte, 1u) != BL_STATUS_OK)
        {
            return BL_STATUS_IO;
        }

        if (read_byte != data[index])
        {
            return BL_STATUS_ERROR;
        }
    }

    return BL_STATUS_OK;
}
