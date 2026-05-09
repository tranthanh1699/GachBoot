# Signature Key Injection

The target firmware does not parse PEM. Convert `publickey.pem` on the host
during the build and inject the generated macros into `bl_signature.c`.

## Project Build Targets

The repository root `Makefile` provides two bootloader build modes:

```sh
make dev
```

Builds the development bootloader with signature verification disabled:

```c
BL_ENABLE_SIGNATURE_VERIFY=0u
```

```sh
make release
```

Builds the release bootloader with signature verification enabled. The release
build converts the PEM public key into a generated C header before compiling
`bl_signature.c`.

Default release key path:

```text
../RSA_Key/public_key.pem
```

Override the key path:

```sh
make release PUBLIC_KEY_PEM=/path/to/publickey.pem
```

Generated release key header:

```text
build/Release/bl_rsa_public_key_generated.h
```

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

Release builds require:

```cmake
target_compile_definitions(bootloader PRIVATE
    BL_ENABLE_SIGNATURE_VERIFY=1u
    BL_RSA_PUBLIC_KEY_HEADER="${CMAKE_BINARY_DIR}/bl_rsa_public_key_generated.h"
)
```

Development builds compile with:

```cmake
BL_ENABLE_SIGNATURE_VERIFY=0u
```

## Notes

- `publickey.pem` is used only by the host build.
- The STM32 target receives only the generated constants.
- No OpenSSL, file IO, malloc, or PEM parser is used on target.
