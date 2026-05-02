# Memory Map

| Region | Start | Size |
|---|---:|---:|
| Bootloader | `0x08000000` | `0x00020000` |
| Application | `0x08020000` | `0x001C0000` |
| Metadata | `0x081FF000` | pending final layout |

The memory service refuses writes outside the application range.

The linker script is not changed in this milestone. Production use must align the linker script, vector table, and flashing tool metadata with this map.
