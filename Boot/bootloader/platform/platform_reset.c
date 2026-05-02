#include "platform_reset.h"
#include "stm32h7xx_hal.h"

void platform_reset_mcu(void)
{
    NVIC_SystemReset();
}
