# GachBoot Flashing Tool

A lightweight Python + Qt6 application for flashing application firmware over UART using the GachBoot protocol.

## Features

- Serial port auto-detection
- Handshake with bootloader (HELLO)
- Automatic firmware chunking and CRC32 calculation
- Real-time flashing progress and logs
- Fail-safe abort handling

## Requirements

- Python 3.11+
- PySide6
- pyserial
- pytest (for development)

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/macOS
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python app/main.py
```

1. Select the serial port of the target MCU.
2. Select the firmware binary (.bin).
3. Click **Connect** to perform handshake.
4. Click **Flash** to start the update process.

## Architecture

- `app/`: Application entry point.
- `protocol/`: Frame encoding, decoding, and command definitions.
- `transport/`: Serial and fake transport implementations.
- `firmware/`: Firmware image handling and checksums.
- `services/`: Flashing flow orchestration.
- `ui/`: Qt6 widgets and main window.
- `tests/`: Unit and integration tests.
