#include "bl_app_validate.h"
#include "bl_memory_map.h"

static bool bl_app_address_is_in_range(uint32_t address, uint32_t start_address, uint32_t size)
{
    uint32_t end_address = start_address + size;

    if (end_address < start_address)
    {
        return false;
    }

    return ((address >= start_address) && (address < end_address));
}

static bool bl_app_stack_pointer_is_valid(uint32_t stack_pointer)
{
    if (bl_app_address_is_in_range(stack_pointer, BL_RAM_DTCM_START_ADDR, BL_RAM_DTCM_SIZE) == true)
    {
        return true;
    }

    if (bl_app_address_is_in_range(stack_pointer, BL_RAM_AXI_START_ADDR, BL_RAM_AXI_SIZE) == true)
    {
        return true;
    }

    if (bl_app_address_is_in_range(stack_pointer, BL_RAM_SRAM123_START_ADDR, BL_RAM_SRAM123_SIZE) == true)
    {
        return true;
    }

    if (bl_app_address_is_in_range(stack_pointer, BL_RAM_SRAM4_START_ADDR, BL_RAM_SRAM4_SIZE) == true)
    {
        return true;
    }

    return false;
}

bool bl_app_validate_vector_table(uint32_t app_address)
{
    uint32_t initial_sp;
    uint32_t reset_handler;
    uint32_t app_end = BL_APP_START_ADDR + BL_APP_MAX_SIZE;
    const uint32_t *vector_table = (const uint32_t *)(uintptr_t)app_address;

    if ((app_address < BL_APP_START_ADDR) || (app_address >= (BL_APP_START_ADDR + BL_APP_MAX_SIZE)))
    {
        return false;
    }

    initial_sp = vector_table[0];
    reset_handler = vector_table[1];

    if (bl_app_stack_pointer_is_valid(initial_sp) == false)
    {
        return false;
    }

    if ((reset_handler < BL_APP_START_ADDR) || (reset_handler >= app_end))
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
    const uint32_t *metadata = (const uint32_t *)(uintptr_t)BL_APP_METADATA_ADDR;

    if (metadata[0] != BL_APP_VALID_MARKER)
    {
        return false;
    }

    return bl_app_validate_vector_table(app_address);
}
