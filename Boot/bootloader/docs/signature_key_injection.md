# Signature Key Injection

The target firmware does not parse PEM. Convert `publickey.pem` on the host
during the build and inject the generated macros into `bl_signature.c`.

## Project Build Targets

The repository root `Makefile` provides two bootloader build modes.

### Development bootloader

```sh
make dev
```

This builds a development bootloader with signature verification disabled:

```c
BL_ENABLE_SIGNATURE_VERIFY=0u
```

Use this build while bringing up the board, validating UART flashing, or testing
unsigned packages.

Behavior in Development build:

- RSA signature verification is skipped.
- The bootloader still parses the signed package structure.
- CRC and protocol checks still run.
- `DOWNLOAD_END` does not require a configured RSA public key.

### Release bootloader

```sh
make release
```

This builds an optimized Release bootloader. Secure boot is disabled unless the
user explicitly requests it.

Behavior in Release build without secure boot:

- `BL_ENABLE_SECURE_BOOT=0u`
- `BL_ENABLE_SIGNATURE_VERIFY=0u`
- no public key is required
- metadata CRC, valid marker, app-size, and vector-table checks still run

To build a secure Release bootloader:

```sh
make release SECURE_BOOT=ON PUBLIC_KEY_PEM=../RSA_Key/public_key.pem
```

Behavior in Release build with secure boot:

- `BL_ENABLE_SECURE_BOOT=1u`
- `BL_ENABLE_SIGNATURE_VERIFY=1u`
- RSA-2048 / SHA-256 signature verification is required on every boot
- The SHA-256 digest is built incrementally while valid application bytes are
  received and written during `DATA` processing.
- `DOWNLOAD_END` finalizes the digest and verifies the signature before marking
  the application valid.
- On normal startup, the bootloader re-hashes the installed application using
  `app_size` from metadata and verifies the stored signature before jumping.

Default release key path:

```text
../RSA_Key/public_key.pem
```

Override the key path:

```sh
make release SECURE_BOOT=ON PUBLIC_KEY_PEM=/path/to/public_key.pem
```

Generated release key header:

```text
build/Release/bl_rsa_public_key_generated.h
```

## How To Add Or Replace The Bootloader Public Key

1. Generate or obtain an RSA-2048 public key in PEM format.
2. Place the PEM file at the default location:

```text
../RSA_Key/public_key.pem
```

   or pass a custom path when building release:

```sh
make release SECURE_BOOT=ON PUBLIC_KEY_PEM=/absolute/or/relative/path/to/public_key.pem
```

3. Run the secure release build with `SECURE_BOOT=ON`. The host build converts
   the PEM file into generated C constants and injects them into the bootloader build.
4. Flash the resulting Release bootloader image to the target.
5. Sign firmware packages using the matching private key.

If the public key changes, you must rebuild and reflash the Release bootloader.
Firmware signed by an old private key will no longer verify against the new
public key.

## Generic Makefile Pattern

```make
PUBLIC_KEY_PEM := publickey.pem
BUILD_DIR := build
PUBLIC_KEY_HEADER := $(BUILD_DIR)/bl_rsa_public_key_generated.h

$(PUBLIC_KEY_HEADER): $(PUBLIC_KEY_PEM) bootloader/tools/rsa_public_key_from_pem.py
	python3 bootloader/tools/rsa_public_key_from_pem.py --pem $(PUBLIC_KEY_PEM) --out $(PUBLIC_KEY_HEADER)

CFLAGS += -DBL_SIGNATURE_VERIFY_ENABLE=1
CFLAGS += -DBL_RSA_PUBLIC_KEY_HEADER=\"$(PUBLIC_KEY_HEADER)\"
CFLAGS += -I$(BUILD_DIR)

bootloader/security/bl_signature.o: $(PUBLIC_KEY_HEADER)
```

The generated header provides:

```c
#define BL_RSA_PUBLIC_KEY_N0INV ...
#define BL_RSA_PUBLIC_KEY_N_WORDS ...
#define BL_RSA_PUBLIC_KEY_RR_WORDS ...
```

The public key must be RSA-2048 with public exponent `65537`.

## CMake Integration

The current CMake project implements the release flow in
`bootloader/CMakeLists.txt`.

Secure Release builds require:

```cmake
target_compile_definitions(bootloader PRIVATE
    BL_ENABLE_SECURE_BOOT=1u
    BL_ENABLE_SIGNATURE_VERIFY=1u
    BL_RSA_PUBLIC_KEY_HEADER="${CMAKE_BINARY_DIR}/bl_rsa_public_key_generated.h"
)
```

Development and non-secure Release builds compile with:

```cmake
BL_ENABLE_SECURE_BOOT=0u
BL_ENABLE_SIGNATURE_VERIFY=0u
```

## Notes

- `publickey.pem` is used only by the host build.
- The STM32 target receives only the generated constants.
- No OpenSSL, file IO, malloc, or PEM parser is used on target.
