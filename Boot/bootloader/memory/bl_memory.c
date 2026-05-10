#include "bl_memory.h"
#include "bl_flash.h"
#include "bl_memory_map.h"
#include <string.h>

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

bl_status_t bl_memory_invalidate_application_marker(void)
{
    return bl_flash_invalidate_app_marker();
}

bl_status_t bl_memory_mark_application_valid(const uint8_t *signature, uint16_t signature_length)
{
    return bl_flash_mark_app_valid(signature, signature_length);
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
    const uint8_t *flash_data = (const uint8_t *)(uintptr_t)address;

    if (data == (const uint8_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    if (bl_memory_range_is_valid(address, length) == false)
    {
        return BL_STATUS_PARAM;
    }

    if (memcmp(flash_data, data, (size_t)length) != 0)
    {
        return BL_STATUS_ERROR;
    }

    return BL_STATUS_OK;
}
