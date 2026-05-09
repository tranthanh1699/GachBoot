#include "platform_uart.h"
#include "bl_config.h"
#include "bl_hw_config.h"
#include "usart.h"

static uint8_t platform_uart_rx_buffer[BL_UART_RX_BUFFER_SIZE];
static volatile uint16_t platform_uart_rx_head;
static volatile uint16_t platform_uart_rx_tail;
static volatile uint32_t platform_uart_rx_overflow_count;
static uint8_t platform_uart_rx_byte;

static uint16_t platform_uart_next_index(uint16_t index)
{
    uint16_t next_index = (uint16_t)(index + 1u);

    if (next_index >= BL_UART_RX_BUFFER_SIZE)
    {
        next_index = 0u;
    }

    return next_index;
}

bl_status_t platform_uart_init(void)
{
    platform_uart_rx_buffer_reset();

    if (HAL_UART_Receive_IT(&huart1, &platform_uart_rx_byte, 1u) != HAL_OK)
    {
        return BL_STATUS_IO;
    }

    return BL_STATUS_OK;
}

bl_status_t platform_uart_read_byte(uint8_t *byte)
{
    uint16_t tail;

    if (byte == (uint8_t *)0)
    {
        return BL_STATUS_PARAM;
    }

    tail = platform_uart_rx_tail;
    if (tail == platform_uart_rx_head)
    {
        return BL_STATUS_TIMEOUT;
    }

    *byte = platform_uart_rx_buffer[tail];
    platform_uart_rx_tail = platform_uart_next_index(tail);

    return BL_STATUS_OK;
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

bl_status_t platform_uart_rx_isr_push_byte(uint8_t byte)
{
    uint16_t head = platform_uart_rx_head;
    uint16_t next_head = platform_uart_next_index(head);

    if (next_head == platform_uart_rx_tail)
    {
        platform_uart_rx_overflow_count++;
        return BL_STATUS_BUSY;
    }

    platform_uart_rx_buffer[head] = byte;
    platform_uart_rx_head = next_head;
    return BL_STATUS_OK;
}

void platform_uart_rx_buffer_reset(void)
{
    uint16_t index = 0u;

    platform_uart_rx_head = 0u;
    platform_uart_rx_tail = 0u;
    platform_uart_rx_overflow_count = 0u;

    for (index = 0u; index < BL_UART_RX_BUFFER_SIZE; index++)
    {
        platform_uart_rx_buffer[index] = 0u;
    }
}

uint32_t platform_uart_rx_get_overflow_count(void)
{
    return platform_uart_rx_overflow_count;
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart == &huart1)
    {
        (void)platform_uart_rx_isr_push_byte(platform_uart_rx_byte);
        (void)HAL_UART_Receive_IT(&huart1, &platform_uart_rx_byte, 1u);
    }
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if (huart == &huart1)
    {
        (void)HAL_UART_Receive_IT(&huart1, &platform_uart_rx_byte, 1u);
    }
}
