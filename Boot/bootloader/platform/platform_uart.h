#ifndef PLATFORM_UART_H
#define PLATFORM_UART_H

#include "bl_types.h"

bl_status_t platform_uart_init(void);
bl_status_t platform_uart_read_byte(uint8_t *byte);
bl_status_t platform_uart_write(const uint8_t *data, uint16_t length);
uint32_t platform_uart_get_tick_ms(void);
bl_status_t platform_uart_rx_isr_push_byte(uint8_t byte);
void platform_uart_rx_buffer_reset(void);
uint32_t platform_uart_rx_get_overflow_count(void);

#endif /* PLATFORM_UART_H */
