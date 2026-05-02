# Porting Guide

Porting should be limited to:

- `config/bl_memory_map.h`
- `config/bl_hw_config.h`
- `platform/platform_uart.c`
- `platform/platform_flash.c`
- `platform/platform_reset.c`

Protocol code must not access MCU registers or vendor HAL APIs directly.

Required platform behavior:

- UART RX interrupt path feeds bytes with `platform_uart_rx_isr_push_byte()`.
- UART read byte returns `BL_STATUS_TIMEOUT` when no buffered byte is available.
- UART write sends all bytes or returns `BL_STATUS_IO`.
- Flash write must validate target alignment and preserve bootloader flash.
- Reset must not return.
