# Porting Guide

Porting should be limited to:

- `config/bl_memory_map.h`
- `config/bl_hw_config.h`
- `platform/platform_boot_mode.c`
- `platform/platform_uart.c`
- `platform/platform_flash.c`
- `platform/platform_reset.c`
- `app/bl_app_jump.c`

Protocol code must not access MCU registers or vendor HAL APIs directly.

Required platform behavior:

- Boot-mode GPIO init must configure the selected input before the boot
  decision is evaluated.
- Boot-mode GPIO read must return true only when the board requests flashing
  mode.
- UART RX interrupt path feeds bytes with `platform_uart_rx_isr_push_byte()`.
- UART init must start interrupt-driven receive before the main loop waits for
  protocol frames.
- UART read byte returns `BL_STATUS_TIMEOUT` when no buffered byte is available.
- UART write sends all bytes or returns `BL_STATUS_IO`.
- Flash write must validate target alignment and preserve bootloader flash.
- Flash metadata helpers must erase the metadata sector and write
  `BL_APP_VALID_MARKER` only after application validation succeeds.
- Jump-to-application must leave the MCU in a state acceptable to the
  application before setting MSP, VTOR, and branching to the reset handler.
- Reset must not return.

Default boot-mode pin configuration:

```c
#define BL_BOOT_MODE_GPIO_PORT           GPIOC
#define BL_BOOT_MODE_GPIO_PIN            GPIO_PIN_13
#define BL_BOOT_MODE_GPIO_PULL           GPIO_PULLUP
#define BL_BOOT_MODE_ACTIVE_STATE        GPIO_PIN_RESET
```

Change these macros for board-specific button wiring.
