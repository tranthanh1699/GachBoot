#include "bl_app_validate.h"
#include "bl_memory_map.h"

bool bl_app_validate_vector_table(uint32_t app_address)
{
    uint32_t initial_sp;
    uint32_t reset_handler;
    uint32_t sram_end = BL_SRAM_BASE_ADDR + BL_SRAM_SIZE;
    uint32_t flash_end = BL_FLASH_BASE_ADDR + BL_FLASH_SIZE;
    const uint32_t *vector_table = (const uint32_t *)app_address;

    if ((app_address < BL_APP_START_ADDR) || (app_address >= (BL_APP_START_ADDR + BL_APP_MAX_SIZE)))
    {
        return false;
    }

    initial_sp = vector_table[0];
    reset_handler = vector_table[1];

    if ((initial_sp < BL_SRAM_BASE_ADDR) || (initial_sp > sram_end))
    {
        return false;
    }

    if ((reset_handler < BL_APP_START_ADDR) || (reset_handler >= flash_end))
    {
        return false;
    }

    if ((reset_handler & 0x00000001u) == 0u)
    {
        return false;
    }

    return true;
}
