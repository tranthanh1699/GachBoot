#include "bl_app_jump.h"
#include "bl_app_validate.h"
#include "stm32h7xx_hal.h"

typedef void (*bl_app_entry_t)(void);

static void bl_app_prepare_hardware_for_jump(void)
{
    /* Disable SysTick */
    SysTick->CTRL = 0u;
    SysTick->LOAD = 0u;
    SysTick->VAL = 0u;

    /* Disable all NVIC interrupts */
    for (uint32_t i = 0u; i < 8u; i++)
    {
        NVIC->ICER[i] = 0xFFFFFFFFu;
        NVIC->ICPR[i] = 0xFFFFFFFFu;
    }

    /* Disable MPU */
    HAL_MPU_Disable();

    /* Flush and disable Caches if they were enabled */
    SCB_DisableICache();
    SCB_DisableDCache();
}

bl_status_t bl_app_jump_to_application(uint32_t app_address)
{
    uint32_t initial_sp;
    uint32_t reset_handler;
    const uint32_t *vector_table = (const uint32_t *)(uintptr_t)app_address;
    bl_app_entry_t app_entry;

    if (bl_app_validate_vector_table(app_address) == false)
    {
        return BL_STATUS_INVALID_STATE;
    }

    initial_sp = vector_table[0];
    reset_handler = vector_table[1];
    app_entry = (bl_app_entry_t)(uintptr_t)reset_handler;

    /* Transition sequence */
    __disable_irq();

    /* Reset peripherals to default state */
    HAL_DeInit();

    /* Disable system components that might interfere with the application */
    bl_app_prepare_hardware_for_jump();

    /* Set vector table and stack pointer */
    SCB->VTOR = app_address;
    __DSB();
    __ISB();
    __set_MSP(initial_sp);
    __ISB();

    /* Jump to application Reset_Handler.
     * We do NOT call __enable_irq() here. The application's startup code
     * will enable interrupts when it's ready. */
    app_entry();

    /* Should never reach here */
    return BL_STATUS_ERROR;
}
