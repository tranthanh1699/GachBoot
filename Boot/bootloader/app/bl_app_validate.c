#include "bl_app_validate.h"
#include "bl_memory_map.h"

#define BL_APP_METADATA_CRC32_INIT_VALUE 0xFFFFFFFFu
#define BL_APP_METADATA_CRC32_POLY       0xEDB88320u

static uint32_t bl_app_metadata_crc32_update_byte(uint32_t crc, uint8_t data)
{
    uint8_t bit_index = 0u;

    crc ^= (uint32_t)data;
    for (bit_index = 0u; bit_index < 8u; bit_index++)
    {
        if ((crc & 1u) != 0u)
        {
            crc = (crc >> 1u) ^ BL_APP_METADATA_CRC32_POLY;
        }
        else
        {
            crc >>= 1u;
        }
    }

    return crc;
}

static uint32_t bl_app_metadata_crc32_calculate(const uint8_t *data, uint32_t length)
{
    uint32_t crc = BL_APP_METADATA_CRC32_INIT_VALUE;
    uint32_t index = 0u;

    for (index = 0u; index < length; index++)
    {
        crc = bl_app_metadata_crc32_update_byte(crc, data[index]);
    }

    return ~crc;
}

static bool bl_app_address_is_in_range(uint32_t address, uint32_t start_address, uint32_t size, bool allow_end)
{
    uint32_t end_address = start_address + size;

    if (end_address < start_address)
    {
        return false;
    }

    if (allow_end)
    {
        return ((address >= start_address) && (address <= end_address));
    }
    else
    {
        return ((address >= start_address) && (address < end_address));
    }
}

static bool bl_app_stack_pointer_is_valid(uint32_t stack_pointer)
{
    if (bl_app_address_is_in_range(stack_pointer, BL_RAM_DTCM_START_ADDR, BL_RAM_DTCM_SIZE, true) == true)
    {
        return true;
    }

    if (bl_app_address_is_in_range(stack_pointer, BL_RAM_AXI_START_ADDR, BL_RAM_AXI_SIZE, true) == true)
    {
        return true;
    }

    if (bl_app_address_is_in_range(stack_pointer, BL_RAM_SRAM123_START_ADDR, BL_RAM_SRAM123_SIZE, true) == true)
    {
        return true;
    }

    if (bl_app_address_is_in_range(stack_pointer, BL_RAM_SRAM4_START_ADDR, BL_RAM_SRAM4_SIZE, true) == true)
    {
        return true;
    }

    return false;
}

bool bl_app_validate_vector_table(uint32_t app_address)
{
    uint32_t initial_sp;
    uint32_t reset_handler;
    const uint32_t *vector_table = (const uint32_t *)(uintptr_t)app_address;

    if (bl_app_address_is_in_range(app_address, BL_APP_START_ADDR, BL_APP_MAX_SIZE, false) == false)
    {
        return false;
    }

    initial_sp = vector_table[0];
    reset_handler = vector_table[1];

    if (bl_app_stack_pointer_is_valid(initial_sp) == false)
    {
        return false;
    }

    if (bl_app_address_is_in_range(reset_handler, BL_APP_START_ADDR, BL_APP_MAX_SIZE, false) == false)
    {
        return false;
    }

    if ((reset_handler & 0x00000001u) == 0u)
    {
        return false;
    }

    return true;
}

bool bl_app_validate_application(uint32_t app_address)
{
    const bl_app_metadata_t *metadata = (const bl_app_metadata_t *)(uintptr_t)BL_APP_METADATA_ADDR;
    uint32_t calculated_crc = 0u;

    if (metadata->valid_marker != BL_APP_VALID_MARKER)
    {
        return false;
    }

    calculated_crc = bl_app_metadata_crc32_calculate((const uint8_t *)&metadata->app_size, sizeof(bl_app_metadata_t) - sizeof(uint32_t));
    if (metadata->crc != calculated_crc)
    {
        return false;
    }

    return bl_app_validate_vector_table(app_address);
}
