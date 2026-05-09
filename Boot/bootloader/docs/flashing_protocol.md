# Lightweight UART Flashing Protocol

## UART

- Baudrate: `115200`
- Data bits: `8`
- Parity: none
- Stop bits: `1`
- Flow control: none
- Bootloader transmit timeout: `BL_PLATFORM_UART_TIMEOUT_MS`
  - default: `100 ms`
  - chosen to allow full-size protocol frames at 115200 baud

All fields are little-endian unless stated otherwise.

## Frame

| Field | Size | Description |
|---|---:|---|
| SOF | 1 | `0xA5` |
| Version | 1 | initial value `0x01` |
| Command ID | 1 | command or response ID |
| Sequence | 1 | tool-controlled sequence number |
| Length | 2 | payload length |
| Payload | N | command payload |
| Checksum | 2 | CRC16-CCITT-FALSE over Version through Payload |

CRC16 parameters:

- polynomial: `0x1021`
- initial value: `0xFFFF`
- no reflection
- no final xor

Maximum payload size is `490` bytes. This keeps the maximum `DATA` body at `480` bytes after the 10-byte DATA header, which preserves STM32H7 32-byte flash write alignment.

Firmware CRC32 parameters:

- standard CRC-32/IEEE reflected algorithm
- polynomial: `0xEDB88320`
- initial value: `0xFFFFFFFF`
- final xor: `0xFFFFFFFF`
- check value for ASCII `123456789`: `0xCBF43926`

## Signed Firmware Package

The host signing step may produce one binary package:

```text
[Header App] + [App Binary] + [Header Signature] + [Signature]
```

The package headers are little-endian and are not C native-packed:

| Field | Size | Description |
|---|---:|---|
| Section ID | 2 | `0xA501` for app, `0x5A02` for signature |
| Size | 4 | section data size |
| CRC32 | 4 | CRC32 over section data only |

Package layout:

| Region | Size |
|---|---:|
| App header | 10 |
| App binary | N |
| Signature header | 10 |
| RSA-2048 signature | 256 |

The app header CRC32 covers only the app binary. The signature header CRC32
covers only the signature bytes. The bootloader does not program either package
header to flash.

The flashing tool parses and validates this package on the PC, then maps it onto
the UART protocol:

- `DOWNLOAD_START.Firmware Size` = app binary size
- `DOWNLOAD_START.Firmware CRC32` = app binary CRC32
- `DOWNLOAD_START.Signature Enabled` = `1`
- `DOWNLOAD_START.Signature Length` = `256`
- `DOWNLOAD_START.Signature Data` = RSA signature bytes
- `DATA` frames = app binary bytes only

Signature algorithm:

- RSA-2048
- exponent `65537`
- SHA-256 digest over the app binary only
- PKCS#1 v1.5 encoded signature

## Commands

| Command | ID | Response |
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

## Tool Response Timeouts

The PC flashing tool must use command-specific response timeouts.

The bootloader command handler is synchronous. For long flash operations, the
bootloader does not send an intermediate progress frame; it sends the command
response only after the operation completes.

Recommended minimum response timeouts:

| Command | Minimum timeout | Reason |
|---|---:|---|
| `HELLO` | `1000 ms` | quick protocol negotiation |
| `START_SESSION` | `1000 ms` | local state reset only |
| `ERASE` | `30000 ms` | erases application flash and metadata sector |
| `DOWNLOAD_START` | `1000 ms` | metadata validation only |
| `DATA` | `3000 ms` | flash write plus readback verify for one block |
| `DOWNLOAD_END` | `10000 ms` | full-image CRC32, optional signature check, marker write |
| `ABORT` | `1000 ms` | local state reset only |
| `RESET` | `1000 ms` | response is sent before MCU reset |

If the tool reports a timeout such as `Timeout waiting for SOF of ERASE
response`, the most likely cause is that the tool used a short generic timeout
while the target was still erasing flash. The tool should not retry or reset the
target immediately on an `ERASE` response timeout unless the configured
long-operation timeout has elapsed.

The timeout values above are minimums. Increase them for slower clock settings,
larger application regions, lower supply voltage flash timing, or additional
verification work.

## Error Codes

| Code | Meaning |
|---:|---|
| `0x00` | OK |
| `0x01` | Invalid frame |
| `0x02` | Unsupported protocol version |
| `0x03` | Unsupported command |
| `0x04` | Invalid sequence number |
| `0x05` | Invalid payload length |
| `0x06` | Checksum mismatch |
| `0x07` | Session not active |
| `0x08` | Flash erase failed |
| `0x09` | Flash write failed |
| `0x0A` | Flash verify failed |
| `0x0B` | Firmware size invalid |
| `0x0C` | Firmware checksum invalid |
| `0x0D` | Firmware signature invalid |
| `0x0E` | Timeout |
| `0x0F` | Internal error |
| `0x10` | Abort requested |

`ERROR_RESPONSE` payload:

| Field | Size |
|---|---:|
| Request Command ID | 1 |
| Error Code | 1 |

## HELLO

Request payload:

| Field | Size |
|---|---:|
| Tool Protocol Version | 1 |
| Tool Capability Flags | 4 |

Response payload:

| Field | Size |
|---|---:|
| Bootloader Protocol Version | 1 |
| Bootloader Major | 1 |
| Bootloader Minor | 1 |
| Bootloader Patch | 1 |
| Bootloader Capability Flags | 4 |
| Max Payload Size | 2 |
| Application Start Address | 4 |
| Application Max Size | 4 |

## DOWNLOAD_START

Payload:

| Field | Size |
|---|---:|
| Firmware Size | 4 |
| Firmware CRC32 | 4 |
| Target Address | 4 |
| Signature Enabled | 1 |
| Signature Length | 2 |
| Signature Data | N |

The bootloader rejects metadata if the target range is outside the configured application area.
Release bootloaders also reject `DOWNLOAD_START` if the signature is missing or
not exactly 256 bytes. Development bootloaders accept the metadata but do not
verify the signature.

## DATA

Payload:

| Field | Size |
|---|---:|
| Block Index | 4 |
| Target Offset | 4 |
| Data Length | 2 |
| Data | N |

The bootloader accepts only the next expected block index and offset. Each accepted block is written and read back before the positive response.
Each non-final DATA block must contain a 32-byte aligned data length. With the default 490-byte maximum payload, the recommended data size is 480 bytes per frame. The final DATA block may be shorter and is padded internally for STM32H7 flash-word programming.

Response payload:

| Field | Size |
|---|---:|
| Status | 1 |
| Block Index | 4 |

## DOWNLOAD_END

Request payload: empty.

Response payload:

| Field | Size |
|---|---:|
| Status | 1 |

The bootloader verifies the full app CRC32 over flash before returning OK. In a
Release bootloader, RSA/SHA-256 signature verification must also return OK.
Development bootloaders skip signature verification.
After successful CRC/signature validation, the bootloader writes the application valid marker in the metadata area.

The flashing tool must not include the valid marker in the application image.
For external factory flashing that bypasses this protocol, the factory process
must program the application image, verify it, then program the valid marker
separately according to `memory_map.md`.

## Example HELLO Frame

Request fields:

- SOF: `A5`
- Version: `01`
- Command: `01`
- Sequence: `00`
- Length: `05 00`
- Payload: `01 00 00 00 00`
- CRC16: calculated over `01 01 00 05 00 01 00 00 00 00`

The tool must calculate and append the CRC bytes little-endian.
