# Lightweight UART Bootloader Requirement Review

## Scope Confirmed

This bootloader is a new lightweight UART flashing path under `Boot/bootloader`.
It is intentionally separate from the existing UDS/AUTOSAR-style services.

Initial implementation scope:

- deterministic frame format using SOF `0xA5`
- protocol version `0x01`
- CRC16-CCITT-FALSE frame checksum
- CRC32 firmware checksum contract
- session and abort handling
- portable UART, flash, reset, app-validation interfaces
- buildable module skeleton for later hardware flash integration

## Assumptions

- USART1 is the initial bootloader UART because `Boot/Core/Src/usart.c` already configures USART1 at 115200-8N1.
- Application starts at `0x08020000`, reserving 128 KiB for the bootloader.
- STM32H743 flash erase/write details require target validation before enabling real write/erase.
- Signature verification is disabled by default. When enabled today, the interface returns unsupported instead of pretending to verify cryptography.

## Open Questions

- Final bootloader flash size and linker partition should be confirmed against the production memory map.
- App metadata currently stores only the valid marker word; any expanded metadata layout still needs final definition.
- Boot entry policy now uses a configurable GPIO boot-mode request; timeout or software-flag entry modes remain open extensions.
- Real signature algorithm and key storage policy are not selected.

## Risks

- Flash erase/write on STM32H7 is bank/sector/voltage/alignment sensitive and must not be completed without target testing.
- Main-loop UART polling must not starve existing background tasks.
- Jump-to-application requires vector table, MPU/cache/peripheral state validation on hardware.
- Protocol docs are stable enough for tool development, but expanded metadata details remain future work.
