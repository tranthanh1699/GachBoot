# Bootloader Flow

## State Table

| State | Accepted Commands | Notes |
|---|---|---|
| READY | HELLO, START_SESSION, ABORT | initial state after bootloader init |
| ACTIVE | HELLO, ERASE, DOWNLOAD_START, ABORT, RESET | flash session is open |
| DOWNLOAD | HELLO, DATA, DOWNLOAD_END, ABORT, RESET | metadata accepted, data transfer active |
| ERROR | ABORT, HELLO | implementation resets to READY after abort or timeout |

## Nominal Flashing Flow

1. Tool opens UART.
2. Tool sends `HELLO`.
3. Bootloader returns protocol version, capabilities, max payload, app address, and app size.
4. Tool sends `START_SESSION`.
5. Bootloader clears previous temporary session state.
6. Tool sends `ERASE`.
7. Bootloader erases the application area.
8. Tool sends `DOWNLOAD_START`.
9. Bootloader validates firmware size, target range, checksum mode, and signature metadata.
10. Tool sends sequential `DATA` frames.
11. Bootloader checks frame CRC16, block index, offset, application range, write result, and readback.
12. Tool sends `DOWNLOAD_END`.
13. Bootloader verifies full CRC32.
14. If enabled, bootloader verifies the signature.
15. Bootloader marks the application valid.
16. Tool sends `RESET`.

## Timeout Recovery

If a partial frame times out:

- the active receive buffer is cleared
- the session is aborted
- no application-valid marker is written
- bootloader returns to READY
- the tool may restart from `HELLO`

## Abort Recovery

On `ABORT`:

- session metadata is cleared
- expected block index is reset
- received byte count is reset
- application is not marked valid
- bootloader responds with `ABORT_RESPONSE`

## Current Implementation Status

Implemented:

- frame encode/decode
- CRC16 frame checksum
- HELLO
- START_SESSION
- ABORT
- DOWNLOAD_START metadata validation
- DATA sequencing and callout to memory service
- UART transport receive state machine

Stubbed until hardware validation:

- STM32H7 flash erase/write
- full firmware CRC32 over flash
- valid-marker write
- real signature verification
- final boot decision policy
