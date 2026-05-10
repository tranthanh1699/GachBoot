# AI Session Handoff - Flashing Tool

## 1. Project Area

- Area: Flashing Tool
- AI Role: Senior Python Tool Developer
- Current Milestone: TOOL-6 Hardware Validation & Refinement
- Last Updated: 2026-05-09
- Updated By: AI session

---

## 2. Current High-Level Goal

Develop a Python + Qt6 flashing tool for a custom UART bootloader. The tool is now fully functional and refined after addressing key architectural and integration issues.

---

## 3. Completed Work

- Cleaned up legacy files in `Tool/`.
- Created project structure in `Tool/flashing_tool/`.
- Set up `venv` and `requirements.txt`.
- Implemented **Milestone TOOL-1 (Protocol Core)**:
  - CRC16-CCITT-FALSE.
  - Frame encode/decode with the bootloader's 490-byte maximum payload.
  - Command and Error enums.
  - Unit tests for frame codec.
- Implemented **Milestone TOOL-2 (Firmware Model)**:
  - CRC32 calculation.
  - Firmware image loading and chunking.
  - Signed-package `.bin` loading with application and signature section CRC validation.
  - Support for passing firmware file path as a CLI argument to the GUI.
  - **Automation Scripts**: Added `sign_firmware.sh` and `scripts/sign_firmware.py` for headless key generation and firmware signing.
  - Unit tests for firmware model including signed-package loading and rejection of unsupported file formats.
- Implemented **Milestone TOOL-3 (Serial Transport)**:
  - Base `Transport` abstraction.
  - `SerialTransport` using `pyserial`.
  - `FakeTransport` for testing.
- Implemented **Milestone TOOL-4 (Flash Service)**:
  - `ProtocolClient` for request/response handling.
  - `FlashService` for full protocol flow orchestration.
  - Integration tests for happy path using `FakeTransport`.
- Implemented **Milestone TOOL-5 (Qt6 GUI)**:
  - Main Window (refactored with signals for thread-safe UI updates).
  - Connection Panel (port/baudrate).
  - Firmware Panel (file selection, signature support).
  - Progress Panel (progress bar).
  - Log Panel (text logs).
  - Threaded flashing execution.
- Implemented **Firmware Signing**:
  - `cryptography` requirement added.
  - `FirmwareSigner` implementation with RSA-2048.
  - `DOWNLOAD_START` sends signed-package metadata with signature length `0`; the 256-byte RSA signature is sent as part of the package stream in `DATA`.
- **Bootloader Integration Fixes**:
  - Synced tool frame payload limit to `BL_FRAME_MAX_PAYLOAD_SIZE` (`490`) in the bootloader.
  - Increased `BL_SIGNATURE_MAX_SIZE` to 256 in bootloader.
  - Implemented `DOWNLOAD_END` finalize/verification in bootloader.
  - Added command-specific tool response timeouts for synchronous flash operations.

---

## 4. Partially Completed Work

- **Milestone TOOL-6 (Hardware Validation)**:
  - Not started with real hardware.

---

## 5. Not Started Yet

- CI/CLI mode.
- Advanced retry policies.

---

## 6. Important Design Decisions

- Protocol version: `0x01`.
- SOF: `0xA5`.
- CRC16: CCITT-FALSE (init 0xFFFF, poly 0x1021).
- DATA header size: 10 bytes (Block index 4, Offset 4, Len 2).
- Progress calculation: Based on acknowledged blocks.
- Threading: Flashing runs in a background thread; UI updates must use signals.
- Max Payload: 490 bytes for both tool and bootloader.
- DATA chunking: `max_payload - 10` rounded down to the 32-byte flash write alignment. With the default 490-byte payload, DATA carries 480 signed-package bytes per frame.
- Response timeouts: command-specific; `ERASE` uses 30000 ms and `DOWNLOAD_END` uses 10000 ms.

---

## 7. Protocol Contract Status

- Protocol document: `Boot/bootloader/docs/flashing_protocol.md`
- Flow document: `Boot/bootloader/docs/bootloader_flow.md`
- Status: **Stable** (updated to support RSA signatures and finalization).

---

## 8. Files Modified/Created

```text
Tool/flashing_tool/
├── app/main.py
├── firmware/checksum.py, firmware_image.py, signer.py
├── protocol/commands.py, errors.py, frame.py, protocol_client.py
├── services/flash_service.py
├── transport/transport_base.py, serial_transport.py, fake_transport.py
├── ui/main_window.py, connection_panel.py, firmware_panel.py, progress_panel.py, log_panel.py
├── tests/test_frame.py, test_firmware.py, test_flash_service.py
├── requirements.txt
├── README.md
└── ai_tool_handoff.md

Boot/bootloader/
├── config/bl_config.h, bl_security_config.h
├── core/bl_session.c, bl_session.h
└── protocol/bl_command.c
```

---

## 9. Build and Test Status

```text
Test command:
cd Tool/flashing_tool && ./venv/bin/python -m pytest tests/

Test result:
PASS (10 tests collected)
```

---

## 10. Known Issues and Risks

- Real hardware validation may require timing adjustments for UART.
- Flash erase on STM32H7 is handled with a long command-specific timeout, but the 30000 ms default still needs hardware validation.

---

## 11. Next Recommended Steps

Continue with **Milestone TOOL-6: Hardware Validation**:

1. Connect a real STM32H7 target.
2. Run the tool: `cd Tool/flashing_tool && ./venv/bin/python app/main.py`.
3. Test a full flash cycle with RSA signing enabled.
4. Verify the bootloader jumps to the application correctly.
