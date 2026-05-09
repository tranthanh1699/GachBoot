# Boot Entry Policy

## Goal

The bootloader must support field flashing through a hardware input while still
booting a valid application automatically during normal startup.

If the application is missing, unavailable, erased, unmarked, or invalid, the
bootloader must remain in a waiting state ready to flash.

## Decision Inputs

Boot decision uses:

- boot-mode GPIO input
- application valid marker
- application vector table validation

The default boot-mode GPIO configuration is defined in
`bootloader/config/bl_hw_config.h`:

```c
#define BL_BOOT_MODE_GPIO_PORT           GPIOC
#define BL_BOOT_MODE_GPIO_PIN            GPIO_PIN_13
#define BL_BOOT_MODE_GPIO_PULL           GPIO_PULLUP
#define BL_BOOT_MODE_ACTIVE_STATE        GPIO_PIN_RESET
```

With this default, pressing an active-low button requests bootloader mode.

## Startup Sequence

1. Initialize HAL.
2. Configure clocks.
3. Initialize GPIO.
4. Configure the boot-mode GPIO.
5. Read the boot-mode GPIO.
6. If boot mode is requested, initialize the bootloader transport and wait for
   flashing commands.
7. If boot mode is not requested, validate the application marker.
8. If the marker is valid, validate the application vector table.
9. If validation succeeds, jump to the application.
10. If validation fails, initialize the bootloader transport and wait for
    flashing commands.

## Application Validation

The application is bootable only when all checks pass:

- `BL_APP_VALID_MARKER` exists at `BL_APP_METADATA_ADDR`
- initial stack pointer is inside a configured RAM region
- reset handler is inside the application flash range
- reset handler has the Thumb bit set

The bootloader does not jump to an application that is missing the marker, even
if the vector table looks valid.

## Marker Ownership

The valid marker is owned by the bootloader.

The application image must not include the marker, and application runtime code
should not write the marker. The bootloader writes it after:

- all expected bytes are received
- full firmware CRC32 over flash matches metadata
- signature verification succeeds, when enabled

The marker is erased before a new download. A failed, aborted, or timed-out
download therefore cannot leave the old application marked valid.

## Fallback Behavior

If the boot-mode GPIO is not asserted but the application is not bootable, the
bootloader remains active. This is intentional recovery behavior and allows a
blank or corrupted board to be flashed without holding the boot-mode button.

## Porting Notes

For another board:

- choose a GPIO that is stable during reset and early startup
- configure the pull direction to avoid floating input
- set `BL_BOOT_MODE_ACTIVE_STATE` to match button wiring
- verify the level on real hardware before enabling automatic app jump
