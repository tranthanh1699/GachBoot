# Flashing Tool Development Notes

## Response Timeout Policy

Do not use one short response timeout for every command.

The bootloader handles commands synchronously. It receives one command frame,
performs the requested work, then sends one response frame. For flash operations,
that work may take seconds.

Use per-command response timeouts:

| Command | Recommended minimum timeout |
|---|---:|
| `HELLO` | `1000 ms` |
| `START_SESSION` | `1000 ms` |
| `ERASE` | `30000 ms` |
| `DOWNLOAD_START` | `1000 ms` |
| `DATA` | `3000 ms` |
| `DOWNLOAD_END` | `10000 ms` |
| `ABORT` | `1000 ms` |
| `RESET` | `1000 ms` |

The `ERASE` timeout must be long enough for:

- application flash erase
- metadata sector erase
- response frame transmission

If the tool logs `Timeout waiting for SOF of ERASE response`, the tool likely
stopped waiting before flash erase completed. Treat `ERASE` as a long operation
and keep waiting for the response SOF until the `ERASE` timeout expires.

## Retry Behavior

For `ERASE`, avoid automatic immediate retry after a short timeout. Retrying
while the bootloader is still erasing can desynchronize the protocol.

Recommended behavior:

1. Send `ERASE`.
2. Wait for `ERASE_RESPONSE` using the long erase timeout.
3. If timeout expires, close/reopen the serial session or reset the target.
4. Restart from `HELLO`.

## Progress Reporting

Current protocol does not provide erase progress frames. The tool should display
a local progress state such as `Erasing flash...` while waiting for
`ERASE_RESPONSE`.

Do not assume lack of incoming bytes means failure during erase.

## AI Development Reminder

When generating or modifying flashing tools for this bootloader:

- implement command-specific response timeouts
- set `ERASE` timeout much longer than normal command timeout
- keep waiting for response SOF during flash erase
- do not send another command while waiting for a response
- restart from `HELLO` after any long-operation timeout
- keep the application valid marker out of the application image
