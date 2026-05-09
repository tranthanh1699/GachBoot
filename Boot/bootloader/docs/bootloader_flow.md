# Bootloader Flow

## State Table

| State | Accepted Commands | Notes |
|---|---|---|
| READY | HELLO, START_SESSION, ABORT | initial state after bootloader init |
| ACTIVE | HELLO, ERASE, DOWNLOAD_START, ABORT, RESET | flash session is open |
| DOWNLOAD | HELLO, DATA, DOWNLOAD_END, ABORT, RESET | metadata accepted, data transfer active |
| ERROR | ABORT, HELLO | implementation resets to READY after abort or timeout |

## Startup Boot Decision

At reset, the firmware performs the boot decision before initializing the UART
transport:

1. Initialize HAL, clock, and GPIO.
2. Configure the boot-mode input from `bootloader/config/bl_hw_config.h`.
3. Read the boot-mode input.
4. If the input is asserted, remain in the bootloader and wait for flashing.
5. If the input is not asserted, validate the application.
6. If the application is valid, jump to `BL_APP_START_ADDR`.
7. If the application is missing, unavailable, unmarked, or invalid, remain in
   the bootloader and wait for flashing.

Application validation requires both:

- valid marker word at `BL_APP_METADATA_ADDR`
- valid application vector table at `BL_APP_START_ADDR`

The default boot-mode input is active-low:

```c
#define BL_BOOT_MODE_GPIO_PORT           GPIOC
#define BL_BOOT_MODE_GPIO_PIN            GPIO_PIN_13
#define BL_BOOT_MODE_GPIO_PULL           GPIO_PULLUP
#define BL_BOOT_MODE_ACTIVE_STATE        GPIO_PIN_RESET
```

Boards may change these macros to select another pin or active level.

## Nominal Flashing Flow

1. Tool opens UART.
2. Tool sends `HELLO`.
3. Bootloader returns protocol version, capabilities, max payload, app address, and app size.
4. Tool sends `START_SESSION`.
5. Bootloader clears previous temporary session state.
6. Tool sends `ERASE`.
7. Bootloader erases the application area.
8. Bootloader erases the metadata sector, clearing any previous valid marker.
9. Tool sends `DOWNLOAD_START`.
10. Bootloader validates firmware size, target range, checksum mode, and signature metadata.
11. Tool sends sequential `DATA` frames.
12. Bootloader checks frame CRC16, block index, offset, application range, write result, and readback.
13. Tool sends `DOWNLOAD_END`.
14. Bootloader verifies full CRC32.
15. If enabled, bootloader verifies the signature.
16. Bootloader writes the application valid marker.
17. Tool sends `RESET`.

The application image does not contain the valid marker. The bootloader owns the
marker and writes it only after firmware validation succeeds.

`ERASE` is a long-running synchronous command. The bootloader sends the
`ERASE_RESPONSE` only after flash erase and metadata invalidation complete. The
flashing tool must use a long `ERASE` response timeout and continue waiting for
the response SOF while the target is erasing.

## Timeout Recovery

If a partial frame times out:

- the active receive buffer is cleared
- the session is aborted
- no application-valid marker is written
- any marker erased during `ERASE` remains erased
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
- STM32H7 sector erase and 32-byte flash-word write callouts
- DOWNLOAD_END byte count and CRC32 verification
- application valid-marker invalidation and write
- GPIO boot-entry policy
- UART transport receive state machine

Stubbed until hardware validation:

- real signature verification
