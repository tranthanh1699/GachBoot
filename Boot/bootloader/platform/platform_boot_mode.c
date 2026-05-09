#include "platform_boot_mode.h"
#include "stm32h7xx_hal.h"
#include "bl_hw_config.h"

static void platform_boot_mode_enable_gpio_clock(GPIO_TypeDef *gpio_port)
{
    if (gpio_port == GPIOA)
    {
        __HAL_RCC_GPIOA_CLK_ENABLE();
    }
    else if (gpio_port == GPIOB)
    {
        __HAL_RCC_GPIOB_CLK_ENABLE();
    }
    else if (gpio_port == GPIOC)
    {
        __HAL_RCC_GPIOC_CLK_ENABLE();
    }
    else if (gpio_port == GPIOD)
    {
        __HAL_RCC_GPIOD_CLK_ENABLE();
    }
    else if (gpio_port == GPIOE)
    {
        __HAL_RCC_GPIOE_CLK_ENABLE();
    }
    else if (gpio_port == GPIOF)
    {
        __HAL_RCC_GPIOF_CLK_ENABLE();
    }
    else if (gpio_port == GPIOG)
    {
        __HAL_RCC_GPIOG_CLK_ENABLE();
    }
    else if (gpio_port == GPIOH)
    {
        __HAL_RCC_GPIOH_CLK_ENABLE();
    }
    else
    {
        /* Unsupported boot-mode GPIO port: leave clock setup unchanged. */
    }
}

bl_status_t platform_boot_mode_init(void)
{
    GPIO_InitTypeDef gpio_init = {0};

    platform_boot_mode_enable_gpio_clock(BL_BOOT_MODE_GPIO_PORT);

    gpio_init.Pin = BL_BOOT_MODE_GPIO_PIN;
    gpio_init.Mode = GPIO_MODE_INPUT;
    gpio_init.Pull = BL_BOOT_MODE_GPIO_PULL;
    gpio_init.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(BL_BOOT_MODE_GPIO_PORT, &gpio_init);

    return BL_STATUS_OK;
}

bool platform_boot_mode_is_requested(void)
{
    GPIO_PinState pin_state;

    pin_state = HAL_GPIO_ReadPin(BL_BOOT_MODE_GPIO_PORT, BL_BOOT_MODE_GPIO_PIN);
    return (pin_state == BL_BOOT_MODE_ACTIVE_STATE);
}
