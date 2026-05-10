# GachBoot

Lightweight UART bootloader project for STM32H743, with a companion Python + Qt6 flashing tool.

The project is split into two main parts:

- `Boot/`: STM32H743 bootloader firmware in C.
- `Tool/flashing_tool/`: PC flashing tool in Python + Qt6.
- `Tool/firmware_signing_tool/`: Standalone firmware signing and package creation tool.

The current design replaces the old AUTOSAR-style diagnostic stack with a smaller protocol-first bootloader architecture.

## Repository Structure

```text
GachBoot/
├── Boot/                    STM32H743 bootloader firmware
├── Tool/
│   ├── flashing_tool/       Python + Qt6 flashing tool
│   └── firmware_signing_tool/ Standalone signing and package tool
├── tool_ai_handover/        Protocol and workflow handover for tool development
└── README.md                Project overview and usage guide
```

## Boot Firmware

`Boot` contains the STM32CubeIDE/CubeMX generated board support code and the lightweight UART bootloader modules.

### Boot Folder Structure

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

### Bootloader Module Structure

```text
Boot/bootloader/
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

### Boot Runtime Flow

1. `Core/Src/main.c` initializes STM32 HAL, clock, GPIO, USART1, USB, and TIM17.
2. `bl_main_init()` initializes the bootloader session and UART transport.
3. UART RX interrupts feed bytes into the bootloader RX ring buffer.
4. The main loop calls `bl_main_process()`.
5. The transport reads buffered UART bytes and assembles protocol frames.
6. The command layer handles `HELLO`, `START_SESSION`, `ERASE`, `DOWNLOAD_START`, `DATA`, `DOWNLOAD_END`, `ABORT`, and `RESET`.
7. Flashing data is written to the configured application flash area.
8. `DOWNLOAD_END` verifies firmware CRC32 before reporting success.

### Boot UART

Default UART:

```text
USART1
115200 baud
8 data bits
No parity
1 stop bit
No flow control
```

The bootloader transport does not poll `HAL_UART_Receive()`. RX bytes must be pushed from the UART interrupt path into the bootloader ring buffer.

Public UART RX API:

```c
#include "platform_uart.h"

bl_status_t platform_uart_rx_isr_push_byte(uint8_t byte);
void platform_uart_rx_buffer_reset(void);
uint32_t platform_uart_rx_get_overflow_count(void);
```

Example HAL callback:

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

Keep the ISR short. Do not parse frames, write flash, log, or block inside the interrupt.

### Boot Memory Map

Configured in:

```text
Boot/bootloader/config/bl_memory_map.h
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

### Build Boot Firmware

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

If Ninja or `arm-none-eabi-gcc` is missing, install them or update `Boot/CMakePresets.json` and `Boot/cmake/gcc-arm-none-eabi.cmake` for your local environment.

### Boot Host Checks

Some protocol code can be checked on host GCC:

```sh
cd Boot
gcc -std=c11 -Wall -Wextra -Werror \
  -Ibootloader/config -Ibootloader/core -Ibootloader/protocol -Ibootloader/security \
  bootloader/tests/test_frame.c \
  bootloader/security/bl_checksum.c \
  bootloader/protocol/bl_frame.c \
  -o /tmp/bl_test_frame

/tmp/bl_test_frame
```

This validates the frame codec and CRC16 logic only. It does not replace target testing.

## Flashing Tool

`Tool/flashing_tool` is a modular Python + Qt6 desktop application for flashing application firmware over UART using the GachBoot protocol.

It supports:

- serial port connection
- firmware selection
- signed-package `.bin` firmware loading
- CRC32 calculation
- protocol frame encode/decode
- high-level flashing flow
- progress and log UI
- fake transport for tests
- RSA-2048 signing and package creation scripts

### Flashing Tool Structure

```text
Tool/flashing_tool/
├── app/
│   └── main.py              Qt application entry point
├── firmware/
│   ├── firmware_image.py    Loads signed-package .bin files and prepares firmware data
│   ├── checksum.py          CRC32 calculation
│   └── signer.py            RSA-2048 signing helper
├── protocol/
│   ├── commands.py          Command IDs
│   ├── errors.py            Protocol error codes
│   ├── frame.py             Frame encoding and decoding
│   └── protocol_client.py   Request/response handler
├── services/
│   └── flash_service.py     HELLO -> ERASE -> DATA -> DOWNLOAD_END flow
├── transport/
│   ├── transport_base.py    Transport interface
│   ├── serial_transport.py  pyserial transport
│   └── fake_transport.py    Test transport
├── ui/
│   ├── main_window.py
│   ├── connection_panel.py
│   ├── firmware_panel.py
│   ├── progress_panel.py
│   └── log_panel.py
├── tests/                   pytest tests
├── requirements.txt
└── ai_tool_handoff.md
```

### Run The Flashing Tool

From `Tool/flashing_tool/`:

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

On Windows:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app\main.py
```

Basic use:

1. Select the MCU COM/TTY port and baudrate.
2. Click connect.
3. The tool sends `HELLO` and displays bootloader information.
4. Select a signed-package `.bin` firmware file.
5. Click flash.
6. The tool sends `START_SESSION`, `ERASE`, `DOWNLOAD_START`, `DATA`, and `DOWNLOAD_END`.
7. Check progress and logs for the final result.

### Test The Flashing Tool

From `Tool/flashing_tool/`:

```sh
PYTHONPATH=. pytest tests/
```

The tests use `FakeTransport` for protocol and flashing-flow checks without physical hardware.

## Protocol Summary

Authoritative protocol documentation:

- `Boot/bootloader/docs/flashing_protocol.md`
- `Boot/bootloader/docs/bootloader_flow.md`
- `Boot/bootloader/docs/memory_map.md`
- `Boot/bootloader/docs/porting_guide.md`
- `tool_ai_handover/tool_ai_protocol_contract.md`

Default frame:

```text
+---------+---------+---------+----------+--------+---------+----------+
| SOF     | Version | Command | Sequence | Length | Payload | CRC16    |
| 1 byte  | 1 byte  | 1 byte  | 1 byte   | 2 byte | N byte  | 2 byte   |
+---------+---------+---------+----------+--------+---------+----------+
```

Important protocol constraints:

- SOF: `0xA5`
- Protocol version: `0x01`
- Endianness: little-endian
- Frame checksum: CRC16-CCITT-FALSE
- Firmware checksum: CRC32
- Current max payload: `490` bytes
- DATA header size: `10` bytes
- Recommended DATA body size: `480` bytes
- Non-final DATA blocks must be 32-byte aligned for STM32H7 flash writes
- Final DATA block may be shorter and is padded internally by the bootloader

Core commands:

| Command | Request | Response |
|---|---:|---:|
| HELLO | `0x01` | `0x81` |
| START_SESSION | `0x02` | `0x82` |
| ERASE | `0x03` | `0x83` |
| DOWNLOAD_START | `0x04` | `0x84` |
| DATA | `0x05` | `0x85` |
| DOWNLOAD_END | `0x06` | `0x86` |
| RESET | `0x07` | `0x87` |
| ABORT | `0x08` | `0x88` |
| ERROR_RESPONSE | | `0x7F` |

## Customization Guide

### Change UART Settings

Boot firmware:

```text
Boot/Core/Src/usart.c
Boot/Boot.ioc
Boot/bootloader/config/bl_config.h
```

Flashing tool:

```text
Tool/flashing_tool/ui/connection_panel.py
Tool/flashing_tool/transport/serial_transport.py
```

### Change Memory Layout

Edit:

```text
Boot/bootloader/config/bl_memory_map.h
Boot/STM32H743XX_FLASH.ld
```

Make sure the linker script does not place bootloader code inside the application area.

### Change Flash Rules

STM32H7 flash writes require 32-byte flash-word alignment.

Relevant firmware files:

```text
Boot/bootloader/config/bl_hw_config.h
Boot/bootloader/platform/platform_flash.c
Boot/bootloader/core/bl_session.c
```

The flashing tool chunking must remain compatible with the bootloader's reported max payload and alignment rules.

### Add A Protocol Command

Boot firmware:

```text
Boot/bootloader/protocol/bl_protocol.h
Boot/bootloader/protocol/bl_command.c
```

Flashing tool:

```text
Tool/flashing_tool/protocol/commands.py
Tool/flashing_tool/services/flash_service.py
```

### Change Or Add A Transport

Create a new transport class under:

```text
Tool/flashing_tool/transport/
```

It should implement the same interface as `transport_base.py`. Then update `ui/main_window.py` or the service composition layer to use it.

### Enable Logging

Bootloader logging is disabled by default because USART1 is the protocol UART.

Do not enable UART logging on the same UART used for flashing unless the protocol has an explicit log channel or escaping scheme.

Config:

```text
Boot/bootloader/config/bl_config.h
```

### Enable Signature Verification

The bootloader supports RSA-2048 SHA-256 PKCS#1 v1.5 signature verification. Verification is performed on the final `DOWNLOAD_END` command.

Boot firmware:

- `Boot/bootloader/config/bl_security_config.h`: Security settings.
- `Boot/bootloader/security/bl_signature.c`: RSA/SHA-256 implementation.
- `Boot/bootloader/tools/rsa_public_key_from_pem.py`: Public key header generator.

Flashing tool:

- `Tool/flashing_tool/firmware/signer.py`: RSA-2048 signing using `cryptography` library.
- `Tool/flashing_tool/scripts/sign_firmware.py`: Integrated package signing and keygen script.
- `Tool/firmware_signing_tool/firmware_sign_tool.py`: Standalone signing script.


## Current Limitations

- USB CDC is initialized by CubeMX but is not the active bootloader transport (USART1 is primary).
- Full embedded build depends on local ARM GCC and Ninja availability.
- Multi-bank flash support is implemented but requires validation on high-density STM32H7 parts.

## Development Rules

- Keep bootloader changes small and reviewable.
- Validate pointers before dereference.
- Keep protocol logic independent of STM32 HAL.
- Avoid dynamic allocation in bootloader runtime paths.
- Avoid logging on the protocol UART during flashing.
- Use Qt signals/slots for UI updates from flashing worker threads.
- Run focused tests before committing.
