# GachBoot Boot Firmware

## Overview

`Boot` contains the STM32H743 bootloader firmware and the lightweight UART bootloader modules.

The project is intentionally split into:

- STM32CubeIDE / STM32CubeMX generated board support code
- portable bootloader protocol and state logic
- small platform adapters for UART, flash, reset, and application jump

The old AUTOSAR-style UDS stack, generated diagnostic configuration, and old PC tools were removed from this folder.

## Current Folder Structure

```text
Boot/
├── Core/                         STM32CubeMX application and interrupt files
├── Drivers/                      STM32 HAL and CMSIS drivers
├── Middlewares/                  STM32 USB device middleware
├── USB_DEVICE/                   STM32CubeMX USB device glue
├── bootloader/                   Lightweight UART bootloader implementation
├── cmake/                        Toolchain and STM32CubeMX CMake support
├── Boot.ioc                      STM32CubeIDE/CubeMX project configuration
├── CMakeLists.txt                Firmware build entry point
├── CMakePresets.json             CMake configure/build presets
├── STM32H743XX_FLASH.ld          Linker script
└── startup_stm32h743xx.s         Startup assembly
```

## Bootloader Module Structure

```text
bootloader/
├── app/          Application vector validation and jump logic
├── config/       Central bootloader, memory map, hardware, and security config
├── core/         Main bootloader process, session, and state machine
├── docs/         Protocol, memory map, flow, and porting documentation
├── log/          Optional lightweight logging
├── memory/       Memory service and flash abstraction
├── platform/     STM32H743 UART, flash, and reset adapters
├── protocol/     Frame format, command IDs, command dispatcher
├── security/     CRC/checksum and signature verification interface
├── tests/        Host-side focused tests
└── transport/    UART frame receive/transmit state machine
```

## Runtime Flow

1. `Core/Src/main.c` initializes STM32 HAL, clock, and GPIO.
2. `bl_boot_init()` configures the boot-mode GPIO from `bootloader/config/bl_hw_config.h`.
3. If the boot-mode GPIO is asserted, the firmware stays in the bootloader.
4. If the boot-mode GPIO is not asserted and the application marker plus vector table are valid, the firmware jumps to the application.
5. If the application is missing, unmarked, unavailable, or invalid, the firmware initializes USART1, USB, TIM17, and the bootloader protocol.
6. UART RX interrupts feed bytes into the bootloader RX ring buffer.
7. The main loop calls `bl_main_process()`.
8. The command layer handles `HELLO`, `START_SESSION`, `ERASE`, `DOWNLOAD_START`, `DATA`, `DOWNLOAD_END`, `ABORT`, and `RESET`.
9. `DOWNLOAD_END` verifies the firmware CRC32 and writes the application valid marker before reporting success.

Default boot-mode GPIO configuration:

```c
#define BL_BOOT_MODE_GPIO_PORT           GPIOC
#define BL_BOOT_MODE_GPIO_PIN            GPIO_PIN_9
#define BL_BOOT_MODE_GPIO_PULL           GPIO_PULLUP
#define BL_BOOT_MODE_ACTIVE_STATE        GPIO_PIN_RESET
```

Change these macros for a different board or active-high button.

## UART Protocol

Default UART:

```text
USART1
115200 baud
8 data bits
No parity
1 stop bit
No flow control
```

### UART RX Interrupt API

The bootloader transport does not call `HAL_UART_Receive()` in polling mode. UART RX bytes should be pushed into a fixed-size ring buffer from the UART interrupt path.

Public API:

```c
#include "platform_uart.h"

bl_status_t platform_uart_rx_isr_push_byte(uint8_t byte);
void platform_uart_rx_buffer_reset(void);
uint32_t platform_uart_rx_get_overflow_count(void);
```

Expected usage:

- Configure USART1 RX interrupt in STM32CubeIDE/CubeMX or user code.
- For every received byte, call `platform_uart_rx_isr_push_byte(byte)`.
- Keep the ISR short. Do not parse frames, write flash, log, or block inside the interrupt.
- `bl_main_process()` consumes bytes from the ring buffer in the main loop.
- If `platform_uart_rx_get_overflow_count()` increases, the tool is sending faster than the firmware can consume or the buffer is too small.
- Call `platform_uart_rx_buffer_reset()` only before enabling UART RX interrupts or after RX is disabled.

Example using a HAL receive-complete callback:

```c
#include "platform_uart.h"
#include "usart.h"

static uint8_t boot_uart_rx_byte;

void boot_uart_start_rx_interrupt(void)
{
    (void)HAL_UART_Receive_IT(&huart1, &boot_uart_rx_byte, 1u);
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart == &huart1)
    {
        (void)platform_uart_rx_isr_push_byte(boot_uart_rx_byte);
        (void)HAL_UART_Receive_IT(&huart1, &boot_uart_rx_byte, 1u);
    }
}
```

If you use a custom `USART1_IRQHandler()` path instead of HAL callbacks, call `platform_uart_rx_isr_push_byte(received_byte)` after reading the RX data register and clearing the interrupt flag according to the STM32H7 reference manual.

Protocol documentation:

- `bootloader/docs/flashing_protocol.md`
- `bootloader/docs/bootloader_flow.md`
- `bootloader/docs/memory_map.md`
- `bootloader/docs/porting_guide.md`

PC flashing tool handover documents are outside this firmware folder:

```text
../tool_ai_handover/
```

## Memory Map

Configured in:

```text
bootloader/config/bl_memory_map.h
```

Current default:

```text
Bootloader start: 0x08000000
Bootloader size : 0x00020000
App start       : 0x08100000
App max size    : 0x000E0000
Metadata addr   : 0x081E0000
```

Valid stack pointer ranges include STM32H743 DTCM, AXI SRAM, SRAM1/2/3, and SRAM4.

## Build

From `Boot/`:

```sh
cmake --preset Debug
cmake --build --preset Debug
```

Required tools:

- CMake
- Ninja
- `arm-none-eabi-gcc`
- STM32 flashing/debug tools of your choice

If CMake reports that Ninja or `arm-none-eabi-gcc` is missing, install the ARM GCC toolchain and Ninja, or update `CMakePresets.json` and `cmake/gcc-arm-none-eabi.cmake` for your local environment.

## Development vs Release Bootloader

The bootloader supports two security modes.

### Development bootloader

Use the repository root target:

```sh
make dev
```

Development build behavior:

- signature verification is disabled
- UART flashing flow still runs normally
- package structure, protocol, and checksum checks still run
- useful for board bring-up and unsigned test images

### Release bootloader

Use the repository root target:

```sh
make release
```

Release build behavior:

- signature verification is enabled
- the build injects an RSA-2048 public key into the firmware
- **mandatory signature verification** is performed on every boot and reset
  before jumping to the application
- the bootloader computes SHA-256 incrementally while valid application bytes
  are received and written during `DATA`
- `DOWNLOAD_END` finalizes the digest and verifies the RSA signature before the
  valid marker is written

> **Performance Note**: Release bootloader adds several hundred milliseconds
> of boot latency due to mandatory full-image RSA signature verification.

Public key details and override examples are documented in:

```text
bootloader/docs/signature_key_injection.md
```

## Public Key Injection Summary

Release bootloader images do not parse PEM files on target. Instead, the host
build converts a PEM public key into generated C constants that are compiled
into `bootloader/security/bl_signature.c`.

Default key path used by the release build:

```text
../RSA_Key/public_key.pem
```

Override it when needed:

```sh
make release PUBLIC_KEY_PEM=/path/to/public_key.pem
```

If you replace the public key, you must rebuild and reflash the Release
bootloader, and all firmware packages must be signed by the matching private
key.

## Host Checks

Some bootloader protocol code can be checked on host GCC:

```sh
gcc -std=c11 -Wall -Wextra -Werror \
  -Ibootloader/config -Ibootloader/core -Ibootloader/protocol -Ibootloader/security \
  bootloader/tests/test_frame.c \
  bootloader/security/bl_checksum.c \
  bootloader/protocol/bl_frame.c \
  -o /tmp/bl_test_frame

/tmp/bl_test_frame
```

This validates the frame codec and CRC16 logic only. It does not replace target testing.

## How To Customize

### Change UART Settings

Update the STM32CubeMX USART1 configuration and regenerate if needed:

```text
Core/Src/usart.c
Boot.ioc
```

Keep protocol settings synchronized in:

```text
bootloader/config/bl_config.h
```

RX buffering is configured by:

```c
#define BL_UART_RX_BUFFER_SIZE 1024u
```

Use a buffer larger than one complete protocol frame. The default frame maximum is derived from `BL_FRAME_MAX_PAYLOAD_SIZE`.

### Change Memory Layout

Edit:

```text
bootloader/config/bl_memory_map.h
STM32H743XX_FLASH.ld
```

Make sure the linker script does not place bootloader code inside the application area.

### Change Flash Write Rules

STM32H7 flash writes require 32-byte flash-word alignment. The bootloader 
uses `BL_PLATFORM_FLASH_WRITE_ALIGN` to define internal buffer sizes 
for memory safety.

Relevant files:

```text
bootloader/config/bl_hw_config.h
bootloader/platform/platform_flash.c
bootloader/core/bl_session.c
```

### Enable Logging

Logging is disabled by default because USART1 is the protocol UART.

Do not enable UART logging on the same UART used for flashing unless the protocol has an explicit log channel or escaping scheme.

Configuration:

```text
bootloader/config/bl_config.h
```

### Enable Signature Verification

The bootloader supports RSA-2048 SHA-256 PKCS#1 v1.5 signature verification. Verification is performed in `DOWNLOAD_END` before marking the application as valid.

Configuration:

- `bootloader/config/bl_security_config.h`: Enable/disable signature check.
- `bootloader/security/bl_signature.c`: RSA and SHA-256 implementation.
- `bootloader/tools/rsa_public_key_from_pem.py`: Script to generate the public key C header from a PEM file.

To integrate a public key:
```sh
python bootloader/tools/rsa_public_key_from_pem.py public_key.pem > bootloader/config/bl_pubkey.h
```
Then ensure `bl_security_config.h` points to this header.


## Porting To Another MCU

Keep protocol and session code unchanged when possible.

Port these files first:

```text
bootloader/config/bl_memory_map.h
bootloader/config/bl_hw_config.h
bootloader/platform/platform_boot_mode.c
bootloader/platform/platform_uart.c
bootloader/platform/platform_flash.c
bootloader/platform/platform_reset.c
bootloader/app/bl_app_jump.c
```

Do not add MCU register access to `core/`, `protocol/`, `transport/`, or `security/`.

## Current Limitations

- Hardware flash erase/write and multi-bank support are implemented but should be validated on specific H7 variants.
- USB CDC is initialized but not used as a transport.
- Application metadata stores a metadata CRC32, valid marker, and 256-byte RSA signature.

## Development Rules

- Keep bootloader changes small and reviewable.
- Validate pointer inputs before dereference.
- Keep protocol logic independent of STM32 HAL.
- Avoid dynamic allocation in bootloader runtime paths.
- Avoid logging on the protocol UART during flashing.
- Run focused tests before committing.
- `bootloader/docs/release_checklist.md`
