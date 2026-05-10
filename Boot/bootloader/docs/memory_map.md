# Memory Map

| Region | Start | Size |
|---|---:|---:|
| Bootloader | `0x08000000` | `0x00020000` |
| Application | `0x08100000` | `0x000E0000` |
| Metadata sector | `0x081E0000` | CRC32, valid marker, and signature |

## Application Region

The application must be linked at `0x08100000`.

The application image must not be shifted to make room for the valid marker.
The valid marker is outside the application image and is owned by the
bootloader.

The bootloader validates the application vector table at `BL_APP_START_ADDR`
before jumping:

- initial stack pointer must be inside a configured RAM region
- reset handler must be inside the application flash region
- reset handler must be a Thumb address

## Metadata

Current metadata content:

| Offset | Size | Value | Meaning |
|---:|---:|---|---|
| `0x0000` | 4 bytes | CRC32 | CRC32 over valid marker word and stored signature |
| `0x0020` | 4 bytes | `BL_APP_VALID_MARKER` / `0x47424C56` | application passed bootloader validation |
| `0x0040` | 256 bytes | RSA signature | signature from the signed package |

`BL_APP_METADATA_ADDR` is `0x081E0000`.

The STM32H7 flash program operation writes a 32-byte flash word. The bootloader
therefore writes each metadata item on a 32-byte boundary:

- `BL_APP_METADATA_CRC_ADDR`: CRC32 in word 0, remaining words erased
- `BL_APP_VALID_MARKER_ADDR`: valid marker in word 0, remaining words erased
- `BL_APP_SIGNATURE_ADDR`: 256-byte signature, eight flash words

The metadata sector is erased during the `ERASE` command before a new download.
If download, verification, signature verification, timeout recovery, or abort
fails, the marker remains erased and the bootloader will not auto-jump to the
application.

During successful finalization, the bootloader writes the signature first, then
the metadata CRC, then the valid marker last. This keeps the startup decision
fail-safe if power is lost during metadata programming.

For normal UART flashing, only the bootloader writes this marker. For external
factory flashing that bypasses the bootloader protocol, program and verify the
application first, then program the marker separately.

The memory service refuses writes outside the application range.

The linker script is not changed in this milestone. Production use must align the linker script, vector table, and flashing tool metadata with this map.
