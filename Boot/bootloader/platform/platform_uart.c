#include "platform_uart.h"
#include "bl_hw_config.h"
#include "usart.h"

bl_status_t platform_uart_init(void)
{
    return BL_STATUS_OK;
}

bl_status_t platform_uart_read_byte(uint8_t *byte)
{
    HAL_StatusTypeDef hal_status;

    if (byte == (uint8_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    hal_status = HAL_UART_Receive(&huart1, byte, 1u, 0u);
    if (hal_status == HAL_OK)
    {
        return BL_STATUS_OK;
    }

    if (hal_status == HAL_TIMEOUT)
    {
        return BL_STATUS_TIMEOUT;
    }

    return BL_STATUS_IO;
}

bl_status_t platform_uart_write(const uint8_t *data, uint16_t length)
{
    if ((data == (const uint8_t *)0) || (length == 0u))
    {
        return BL_STATUS_PARAM;
    }

    if (HAL_UART_Transmit(&huart1, (uint8_t *)data, length, BL_PLATFORM_UART_TIMEOUT_MS) != HAL_OK)
    {
        return BL_STATUS_IO;
    }

    return BL_STATUS_OK;
}

uint32_t platform_uart_get_tick_ms(void)
{
    return HAL_GetTick();
}
