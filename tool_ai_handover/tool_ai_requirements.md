# Flashing Tool AI Requirements

## Role

The Tool AI must act as a senior Python desktop tool developer with experience in:

- Qt6 desktop applications
- serial communication
- firmware flashing flows
- binary file parsing
- checksum and protocol implementation
- deterministic tests
- clean, maintainable architecture

## Main Goal

Create a lightweight Python + Qt6 flashing tool that flashes application firmware over UART using the bootloader protocol defined by:

```text
Boot/bootloader/docs/flashing_protocol.md
Boot/bootloader/docs/bootloader_flow.md
```

## Required Technology

- Language: Python 3.11+
- GUI: Qt6, preferably PySide6 unless project policy later chooses PyQt6
- Serial transport: pyserial
- Tests: pytest
- Packaging: define later after core tool works

Do not implement the tool inside `Boot`.

Recommended folder:

```text
Tool/flashing_tool/
```

## Required Features

- Select serial port.
- Configure baudrate, default `115200`.
- Open and close UART connection.
- Select firmware binary file.
- Show firmware size and CRC32.
- Send `HELLO`.
- Start flashing session.
- Erase application area.
- Send firmware metadata using `DOWNLOAD_START`.
- Split firmware into protocol-compliant data blocks.
- Send sequential `DATA` frames.
- Track progress by bytes acknowledged.
- Send `DOWNLOAD_END`.
- Send `RESET` when requested by the user.
- Send `ABORT` on user cancel or fatal flashing failure.
- Show concise logs for TX, RX, progress, and errors.
- Decode and display bootloader error codes.

## Optional Features

- Firmware signing support.
- Saved connection settings.
- CLI flashing mode for CI.
- Dry-run mode using a simulated bootloader transport.

## Safety Requirements

- Never continue flashing after a protocol error unless retry policy explicitly allows it.
- Never ignore `ERROR_RESPONSE`.
- Always verify response command ID, sequence, and payload length.
- Always timeout serial operations.
- Always close serial port on exit.
- On cancel, send `ABORT` if the connection is open.
- Do not mark a flash operation successful unless `DOWNLOAD_END_RESPONSE` returns OK.

## Test Requirements

At minimum, Tool AI must add tests for:

- CRC16-CCITT-FALSE frame checksum.
- Frame encode/decode.
- Bad checksum rejection.
- Error response decoding.
- Firmware CRC32 calculation.
- Firmware chunking boundaries.
- Protocol client happy path using fake transport.
- Abort path using fake transport.
- Timeout path using fake transport.

## Out of Scope for First Tool Milestone

- Real cryptographic signing UI.
- Firmware package formats beyond signed-package `.bin`.
- Vendor-specific flashing outside this custom protocol.
- Replacing CubeIDE or building firmware.
