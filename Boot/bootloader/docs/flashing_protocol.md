# Lightweight UART Flashing Protocol

## UART

- Baudrate: `115200`
- Data bits: `8`
- Parity: none
- Stop bits: `1`
- Flow control: none

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

Maximum payload size is `256` bytes.

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

## DATA

Payload:

| Field | Size |
|---|---:|
| Block Index | 4 |
| Target Offset | 4 |
| Data Length | 2 |
| Data | N |

The bootloader accepts only the next expected block index and offset. Each accepted block is written and read back before the positive response.

Response payload:

| Field | Size |
|---|---:|
| Status | 1 |
| Block Index | 4 |

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
