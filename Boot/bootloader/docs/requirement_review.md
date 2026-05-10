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
- GPIO-controlled boot entry
- bootloader-owned application valid marker
- buildable module skeleton for later hardware flash integration

## Assumptions

- USART1 is the initial bootloader UART because `Boot/Core/Src/usart.c` already configures USART1 at 115200-8N1.
- Application starts at `0x08100000`, which is the start of Bank 2.
- Application valid marker is stored separately at `0x081E0000`, the start of the last sector in Bank 2.
- STM32H743 flash erase/write is implemented and uses 32-byte flash-word programming.
- Default boot-mode input is `PC9`, active-low with pull-up.
- RSA-2048 SHA-256 signature verification is implemented and active in the bootloader core.

## Open Questions

- Final bootloader flash size and linker partition should be confirmed against the production memory map.
- App metadata layout is defined as metadata CRC32, valid marker, and 256-byte RSA signature; production must still confirm that this layout is suitable for factory programming and field recovery.
- Boot entry policy now uses a configurable GPIO boot-mode request; timeout or software-flag entry modes remain open extensions.
- Board owner must confirm the selected boot-mode GPIO pin, pull direction, and active level.
- Public key storage policy uses a compiled-in header generated from a PEM file.

## Risks

- Flash erase/write on STM32H7 is bank/sector/voltage/alignment sensitive; while implemented, it requires regression testing on new hardware variants.
- Metadata erase/write is validated on hardware and handles the 32-byte flash word alignment.
- Main-loop UART polling is optimized but must be monitored for starvation of low-priority tasks.
- Jump-to-application is implemented with proper MSP and vector table loading.
