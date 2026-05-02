# Tool AI Flashing Flow

## User Flow

1. User starts the flashing tool.
2. Tool lists available serial ports.
3. User selects port and baudrate.
4. User selects firmware `.bin`.
5. Tool displays firmware size and CRC32.
6. User clicks connect.
7. Tool sends `HELLO`.
8. Tool displays bootloader version, max payload, application address, and capabilities.
9. User clicks flash.
10. Tool runs the protocol flashing flow.
11. Tool shows progress, logs, and final verdict.
12. User may click reset after successful flashing.

## Protocol Flow

```text
open serial
send HELLO
wait HELLO_RESPONSE
validate protocol version
validate max payload

send START_SESSION
wait START_SESSION_RESPONSE OK

send ERASE
wait ERASE_RESPONSE OK

calculate firmware CRC32
send DOWNLOAD_START
wait DOWNLOAD_START_RESPONSE OK

for each firmware block:
    send DATA
    wait DATA_RESPONSE OK
    verify acknowledged block index
    update progress

send DOWNLOAD_END
wait DOWNLOAD_END_RESPONSE OK

optional:
    send RESET
    wait RESET_RESPONSE OK
```

## Error Flow

On any of these:

- frame decode failure
- timeout
- unexpected command ID
- unexpected sequence number
- `ERROR_RESPONSE`
- non-OK status
- serial disconnect
- user cancel

Tool behavior:

1. Stop current flash operation.
2. If serial port is still open, send `ABORT`.
3. Wait briefly for `ABORT_RESPONSE`, but do not block shutdown forever.
4. Report the exact failing command and error code.
5. Leave UI in a state where user can retry from `HELLO`.

## Retry Policy

First implementation should not retry writes automatically.

Allowed retry:

- HELLO may be retried by user action.
- Frame receive may wait until timeout.

Not allowed in first implementation:

- silently resending DATA after a flash write error
- continuing after invalid sequence
- continuing after checksum mismatch

## Progress Calculation

Progress is based on acknowledged bytes:

```text
progress_percent = acknowledged_bytes * 100 / firmware_size
```

Only increase progress after valid `DATA_RESPONSE`.
