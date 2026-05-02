# GachBoot - Lightweight UART Bootloader Project

## 📋 Project Overview

**GachBoot** is a redesigned, lightweight, and portable bootloader for STM32 microcontrollers (initially STM32H743). This version moves away from heavy AUTOSAR-style abstractions to a modular, "protocol-first" architecture designed for easy porting and reliability.

### Key Components
1.  **Bootloader (C)**: A small-footprint embedded application located in `Boot/bootloader/`.
2.  **Flashing Tool (Python/Qt6)**: A modern desktop application for firmware updates located in `Tool/flashing_tool/`.

---

## 🏗️ Architecture

### 1. Bootloader Structure (`Boot/bootloader/`)
The bootloader is organized into clean, isolated layers:
- `app/`: Application validation and jump logic.
- `config/`: Centralized configuration (Memory map, UART settings, Security).
- `core/`: State machine and session management.
- `protocol/`: Frame parsing and command dispatching.
- `transport/`: UART transport abstraction.
- `platform/`: Hardware-specific drivers (Flash, Reset, UART).
- `security/`: Checksum (CRC16/CRC32) and RSA-2048 signing.

### 2. Flashing Tool Structure (`Tool/flashing_tool/`)
The Python tool follows a similar modular design:
- `app/`: Application entry point.
- `firmware/`: Handles `.bin` and `.hex` files, CRC calculation, and RSA signing.
- `protocol/`: Implementation of the GachBoot frame format.
- `services/`: High-level flashing orchestration (Handshake -> Erase -> Download -> Reset).
- `transport/`: Serial communication backend.
- `ui/`: Qt6-based graphical user interface.

---

## 🚀 Getting Started

### Prerequisites
- **Bootloader**: ARM GCC Toolchain, CMake.
- **Flashing Tool**: Python 3.11+.

### Build the Bootloader
```bash
cd Boot
cmake -B build -G "Unix Makefiles"
cmake --build build
```

### Run the Flashing Tool
1.  Set up the Python environment:
    ```bash
    cd Tool/flashing_tool
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
2.  Launch the GUI:
    ```bash
    python app/main.py
    ```

---

## 🛠️ How to Customize

### Porting to a New MCU
To port the bootloader to a different hardware platform, you only need to modify files in the `platform/` and `config/` directories:
1.  `config/bl_memory_map.h`: Define your new flash and RAM regions.
2.  `platform/platform_uart.c`: Implement UART init, read, and write.
3.  `platform/platform_flash.c`: Implement flash erase and write (ensure proper alignment).
4.  `platform/platform_reset.c`: Implement the system reset trigger.

### Adding New Protocol Commands
1.  **Bootloader**: Add the command ID to `bl_protocol.h` and the handler logic to `bl_command.c`.
2.  **Flashing Tool**: Add the command ID to `protocol/commands.py` and a corresponding method in `services/flash_service.py`.

### Changing Security Settings
- To enable/disable signature verification, toggle `BL_ENABLE_SIGNATURE_VERIFY` in `config/bl_config.h`.
- The tool supports RSA-2048 signing out of the box. To use a different algorithm, update `firmware/signer.py` and the bootloader's `bl_signature.c`.

---

## 📖 Documentation
Detailed technical documentation is available in the `Boot/bootloader/docs/` folder:
- `flashing_protocol.md`: Detailed frame format and command definitions.
- `bootloader_flow.md`: State machine transitions and flashing sequence.
- `memory_map.md`: Expected flash and RAM layout.

---

## 👨‍💻 Author
**Thanh Tran**
- GitHub: [@tranthanh1699](https://github.com/tranthanh1699)
- Repository: [GachBoot](https://github.com/tranthanh1699/GachBoot)

---

**Last Updated:** May 2, 2026
