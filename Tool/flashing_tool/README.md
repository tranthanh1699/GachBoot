# GachBoot Flashing Tool

A lightweight, modular Python + Qt6 application designed for flashing application firmware over UART. It implements the custom GachBoot protocol and supports features like RSA firmware signing and automatic Intel HEX to Binary conversion.

---

## 1. Project Structure

The tool follows a layered architecture to separate protocol logic from UI and hardware transport.

```text
flashing_tool/
├── app/
│   └── main.py              # Entry point. Initializes the Qt application.
├── firmware/
│   ├── firmware_image.py    # Loads .bin/.hex/.ihex/.ihx, calculates CRC32, and handles signing.
│   ├── checksum.py          # CRC32 calculation logic.
│   └── signer.py            # RSA-2048 signing implementation using the 'cryptography' library.
├── protocol/
│   ├── commands.py          # Enum of all supported Command IDs.
│   ├── errors.py            # Enum of Protocol Error Codes.
│   ├── frame.py             # Frame encoding (SOF, Version, Command, Seq, Len, Payload, CRC16).
│   └── protocol_client.py   # Request/Response handler with timeout and sequence management.
├── services/
│   └── flash_service.py     # High-level orchestration of the flashing flow (HELLO -> ERASE -> DATA -> END).
├── transport/
│   ├── transport_base.py    # Abstract base class for all transports.
│   ├── serial_transport.py  # Implementation using 'pyserial'.
│   └── fake_transport.py    # Simulated transport used for unit and integration testing.
├── ui/
│   ├── main_window.py       # Main Qt layout; connects UI signals to the background flashing thread.
│   ├── connection_panel.py  # Serial port selection and connect/disconnect controls.
│   ├── firmware_panel.py    # File selection, RSA signing options, and flash button.
│   ├── progress_panel.py    # Progress bar and status text.
│   └── log_panel.py         # Scrollable text log for communication and debugging.
├── tests/                   # Full test suite using 'pytest'.
├── requirements.txt         # Project dependencies.
└── ai_tool_handoff.md       # Technical handoff for AI-assisted development.
```

---

## 2. How to Use

### Setup
1.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Tool
1.  Launch the application:
    ```bash
    python app/main.py
    ```
2.  **Connection**: Select your MCU's COM/TTY port and baudrate (default 115200). Click **Connect**. The tool sends a `HELLO` command; if successful, it displays the bootloader version.
3.  **Firmware**: Browse for a raw `.bin`, `.hex`, `.ihex`, `.ihx`, or signed package `.bin` file.
    - If you select a HEX file, the tool automatically extracts the **Base Address** from the file.
    - If you select a BIN file, the tool uses the default `app_start` address provided by the bootloader.
    - If you select a signed package, the tool validates the package CRCs and sends only the app bytes in `DATA`.
4.  **Security**: For Release bootloaders, flash a signed package or check **Sign Firmware** and select your RSA-2048 private key (`.pem`). The tool sends the signature during the `DOWNLOAD_START` phase.
5.  **Flash**: Click **Flash**. The tool will automatically ERASE the target area, send DATA blocks, and verify the result.

### CLI Shortcuts
You can pre-fill the firmware path by passing it as a command-line argument:
```bash
python app/main.py path/to/your/firmware.hex
```

---

## 3. Automation Scripts

The tool includes a bash script for automating firmware signing and key generation without launching the GUI.

### Generate RSA-2048 Keys
```bash
python scripts/sign_firmware.py keygen --priv my_private_key.pem --pub my_public_key.pem
```

### Sign Firmware Package
Creates a signed package:

```text
[10-byte AppHeader] [App Binary] [10-byte SignatureHeader] [256-byte Signature]
```

The app CRC32 covers only the app binary. The signature CRC32 covers only the signature bytes.

```bash
python scripts/sign_firmware.py \
  --input app.bin \
  --private-key private_key.pem \
  --output app_signed_package.bin \
  --verbose
```

Inspect a package:

```bash
python scripts/sign_firmware.py --inspect app_signed_package.bin
```

Legacy form is still accepted and now writes a signed package:

```bash
python scripts/sign_firmware.py sign <firmware.bin|.hex> <private_key.pem> --output app_signed_package.bin
```

---

## 4. How to Modify & Customize

### Adding a New Protocol Command
1.  **Define Command ID**: Add your command to `protocol/commands.py`.
2.  **Add Logic**:
    - If it's a simple command, add a method to `services/flash_service.py` using `self.client.request_response(Command.YOUR_CMD, payload)`.
    - If the command can take longer than the default response timeout, add its timeout to `protocol/protocol_client.py`.
    - Handle the response status or payload according to your needs.

### Changing the Signature Algorithm
- Modify `firmware/signer.py`.
- Ensure the `sign()` method returns a byte string.
- If the signature size changes, update `BL_SIGNATURE_MAX_SIZE` in the bootloader's `bl_security_config.h` and check if `BL_FRAME_MAX_PAYLOAD_SIZE` needs increasing.

### Updating the UI
- Each section of the window is a separate widget in `ui/`.
- If you add a new panel, instantiate it in `ui/main_window.py` and add it to the layout.
- **Critical**: Use the `FlashSignals` object in `MainWindow` to send data from the background flashing thread to UI widgets. Directly modifying widgets from a thread will cause crashes.

### Implementing a New Transport (e.g., USB-HID, CAN)
1.  Create a new class in `transport/` that inherits from `Transport` (see `transport_base.py`).
2.  Implement `open()`, `close()`, `read()`, `write()`, and `is_open()`.
3.  Update `ui/main_window.py` to instantiate your new transport instead of `SerialTransport`.

---

## 4. Development & Testing

The tool uses `pytest` for validation.

**Run All Tests**:
```bash
PYTHONPATH=. pytest tests/
```

**Testing with Fake Hardware**:
The `tests/test_flash_service.py` uses `FakeTransport` to simulate a bootloader response. You can use this to test protocol flows without needing a physical device.

---

## 5. Protocol Constraints
- **Max Payload**: The tool and bootloader support up to 490 payload bytes per frame.
- **DATA payload**: DATA frames use a 10-byte command payload header, so the recommended binary chunk size is 480 bytes.
- **Response Timeouts**: Use command-specific response timeouts. `ERASE` waits up to 30000 ms and `DOWNLOAD_END` waits up to 10000 ms because the bootloader handles flash operations synchronously.
- **SOF**: `0xA5`.
- **Endianness**: Little-endian for all multibyte fields (Length, CRC16, CRC32, Addresses).
