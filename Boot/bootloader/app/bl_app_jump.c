#include "bl_app_jump.h"
#include "bl_app_validate.h"
#include "stm32h7xx_hal.h"

typedef void (*bl_app_entry_t)(void);

bl_status_t bl_app_jump_to_application(uint32_t app_address)
{
    uint32_t initial_sp;
    uint32_t reset_handler;
    const uint32_t *vector_table = (const uint32_t *)app_address;
    bl_app_entry_t app_entry;

    if (bl_app_validate_vector_table(app_address) == false)
    {
        return BL_STATUS_INVALID_STATE;
    }

    initial_sp = vector_table[0];
    reset_handler = vector_table[1];
    app_entry = (bl_app_entry_t)reset_handler;

    __disable_irq();
    HAL_DeInit();
    SCB->VTOR = app_address;
    __set_MSP(initial_sp);
    __enable_irq();
    app_entry();

    return BL_STATUS_ERROR;
}
