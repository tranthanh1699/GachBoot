# Tool AI Development Plan

## Milestone TOOL-0: Read Handover

Deliverables:

- Confirm protocol constants.
- Confirm open questions.
- Create initial project structure under `Tool/flashing_tool`.

Exit criteria:

- Tool AI can encode a HELLO frame from documentation.

## Milestone TOOL-1: Protocol Core

Deliverables:

- CRC16-CCITT-FALSE implementation.
- Frame encode/decode.
- Command and error enums.
- Unit tests.

Exit criteria:

- Good frame round trip passes.
- Bad checksum is rejected.
- Error response is decoded.

## Milestone TOOL-2: Firmware Model

Deliverables:

- Firmware binary loader.
- CRC32 calculation.
- Chunking into DATA payloads.
- Unit tests for boundary sizes.

Exit criteria:

- Firmware is split into max `480` byte DATA chunks by default, or a lower 32-byte aligned size if the bootloader reports a smaller max payload.

## Milestone TOOL-3: Serial Transport

Deliverables:

- Serial open/close.
- Blocking request/response with timeout.
- Fake transport for tests.

Exit criteria:

- Protocol client happy path passes using fake transport.

## Milestone TOOL-4: Flash Service

Deliverables:

- HELLO, START_SESSION, ERASE, DOWNLOAD_START, DATA, DOWNLOAD_END, ABORT, RESET methods.
- Error mapping and clear exceptions/results.

Exit criteria:

- Full flash flow passes with fake bootloader.
- Abort path passes.

## Milestone TOOL-5: Qt6 GUI

Deliverables:

- Connection panel.
- Firmware selection panel.
- Progress bar.
- Log panel.
- Start, cancel, reset controls.

Exit criteria:

- GUI can run and execute fake flashing flow without real hardware.

## Milestone TOOL-6: Hardware Validation

Deliverables:

- Test against STM32 target.
- Capture logs.
- Document bootloader limitations seen by tool.

Exit criteria:

- HELLO and START_SESSION work on target.
- If flash write is still stubbed, tool reports the correct error and aborts safely.

## Proposed Folder Structure

```text
Tool/flashing_tool/
├── app/
│   ├── main.py
│   └── settings.py
├── firmware/
│   ├── checksum.py
│   ├── firmware_image.py
│   └── chunker.py
├── protocol/
│   ├── commands.py
│   ├── errors.py
│   ├── frame.py
│   └── protocol_client.py
├── services/
│   └── flash_service.py
├── transport/
│   ├── serial_transport.py
│   └── fake_transport.py
├── ui/
│   ├── main_window.py
│   ├── connection_panel.py
│   ├── firmware_panel.py
│   ├── progress_panel.py
│   └── log_panel.py
└── tests/
    ├── test_frame.py
    ├── test_firmware.py
    └── test_flash_service.py
```
