#include "bl_config.h"
#include "bl_app_jump.h"
#include "bl_app_validate.h"
#include "stm32h7xx_hal.h"

typedef void (*bl_app_entry_t)(void);


static void bl_app_prepare_hardware_for_jump(void)
{
    uint32_t index = 0u;

    SysTick->CTRL = 0u;
    SysTick->LOAD = 0u;
    SysTick->VAL = 0u;

    for (index = 0u; index < BL_APP_NVIC_REGISTER_COUNT; index++)
    {
        NVIC->ICER[index] = 0xFFFFFFFFu;
        NVIC->ICPR[index] = 0xFFFFFFFFu;
    }

    /* Disable MPU */
    HAL_MPU_Disable();

    /* Flush and disable Caches if they were enabled */
#if (BL_IS_APP_USE_CACHEABLE == 1)
    SCB_DisableICache();
    SCB_DisableDCache();
#endif
}

bl_status_t bl_app_jump_to_application(uint32_t app_address)
{
    uint32_t app_stack;
    uint32_t app_reset_handler;
    bl_app_entry_t app_entry;

    if (bl_app_validate_vector_table(app_address) == false)
    {
        return BL_STATUS_INVALID_STATE;
    }

    app_stack = *(volatile uint32_t *)app_address;
    app_reset_handler = *(volatile uint32_t *)(app_address + 4U);
    app_entry = (bl_app_entry_t)app_reset_handler;

    /* Transition sequence */
    __disable_irq();
    HAL_RCC_DeInit();
    HAL_DeInit();
    bl_app_prepare_hardware_for_jump();

    SCB->VTOR = app_address;
    __set_MSP(app_stack);
    __DSB();
    __ISB();

    /* Jump to application Reset_Handler.
     * We do NOT call __enable_irq() here. The application's startup code
     * will enable interrupts when it's ready. */
    app_entry();

    return BL_STATUS_ERROR;
}
