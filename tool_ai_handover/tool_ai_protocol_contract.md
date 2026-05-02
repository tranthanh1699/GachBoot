# Tool AI Protocol Contract

This document repeats the stable protocol items needed by the PC tool.
If there is a conflict, `Boot/bootloader/docs/flashing_protocol.md` is authoritative.

## UART Defaults

| Setting | Value |
|---|---|
| Baudrate | `115200` |
| Data bits | `8` |
| Parity | none |
| Stop bits | `1` |
| Flow control | none |

## Frame Format

All multi-byte fields are little-endian.

```text
+---------+---------+---------+----------+--------+---------+----------+
| SOF     | Version | Command | Sequence | Length | Payload | CRC16    |
| 1 byte  | 1 byte  | 1 byte  | 1 byte   | 2 byte | N byte  | 2 byte   |
+---------+---------+---------+----------+--------+---------+----------+
```

Field values:

- SOF: `0xA5`
- Protocol version: `0x01`
- Maximum payload: `256` bytes
- CRC16: CRC16-CCITT-FALSE over `Version`, `Command`, `Sequence`, `Length`, and `Payload`
- CRC16 polynomial: `0x1021`
- CRC16 init: `0xFFFF`
- CRC16 output byte order in frame: little-endian

## Commands

| Name | Request | Response |
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

## Error Response Payload

| Field | Size |
|---|---:|
| Request command ID | 1 |
| Error code | 1 |

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

## HELLO

Request payload:

| Field | Size |
|---|---:|
| Tool protocol version | 1 |
| Tool capability flags | 4 |

Initial tool capability flags may be `0x00000000`.

Response payload:

| Field | Size |
|---|---:|
| Bootloader protocol version | 1 |
| Bootloader major | 1 |
| Bootloader minor | 1 |
| Bootloader patch | 1 |
| Bootloader capability flags | 4 |
| Max payload size | 2 |
| Application start address | 4 |
| Application max size | 4 |

Expected response payload length: `18`.

## START_SESSION

Request payload: empty.

Response payload:

| Field | Size |
|---|---:|
| Status | 1 |

## ERASE

Request payload: empty.

Response payload:

| Field | Size |
|---|---:|
| Status | 1 |

## DOWNLOAD_START

Request payload:

| Field | Size |
|---|---:|
| Firmware size | 4 |
| Firmware CRC32 | 4 |
| Target address | 4 |
| Signature enabled | 1 |
| Signature length | 2 |
| Signature data | N |

Response payload:

| Field | Size |
|---|---:|
| Status | 1 |

## DATA

Request payload:

| Field | Size |
|---|---:|
| Block index | 4 |
| Target offset | 4 |
| Data length | 2 |
| Data | N |

The tool must calculate `N` so total DATA payload is no more than max payload.
With a 10-byte DATA header and max payload 256, max binary data per frame is `246` bytes.

Response payload:

| Field | Size |
|---|---:|
| Status | 1 |
| Block index | 4 |

## DOWNLOAD_END

Request payload: empty for first implementation.

Response payload:

| Field | Size |
|---|---:|
| Status | 1 |

Note: bootloader finalization is still under development. Tool must handle `ERROR_RESPONSE`.

## RESET

Request payload: empty.

Response payload:

| Field | Size |
|---|---:|
| Status | 1 |

After RESET response, target may reboot and serial connection may drop.

## ABORT

Request payload: empty.

Response payload:

| Field | Size |
|---|---:|
| Status | 1 |
