# Bootloader Release Checklist

When deploying a secure production bootloader to hardware, follow this checklist to ensure the hardware enforces RSA-2048/SHA-256 signatures using secure boot.

### 1. Generate an RSA-2048 Key Pair
Generate a private key and its corresponding public key using standard tools (e.g., OpenSSL).
```sh
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -in private_key.pem -pubout -out public_key.pem
```
Keep `private_key.pem` secure. This is required for signing firmware updates.

### 2. Inject Public Key & Build Release Bootloader
Place your `public_key.pem` in the default directory (`../RSA_Key/public_key.pem`) or pass its path to the build system.

Build the secure Release bootloader from the root directory:
```sh
make release SECURE_BOOT=ON
# OR
make release SECURE_BOOT=ON PUBLIC_KEY_PEM=/path/to/public_key.pem
```
During the build, the python script `bootloader/tools/rsa_public_key_from_pem.py` translates the PEM file into a generated C-header (`bl_rsa_public_key_generated.h`) that the bootloader compiles in.

### 3. Flash the Release Bootloader
Flash the compiled Release bootloader image (`Boot/build/Release/bootloader.elf` or `.bin`/`.hex`) to the STM32H7.
- **Note**: A Release bootloader only enforces signatures when built with `SECURE_BOOT=ON`.
- **Boot Warning**: Secure boot triggers full RSA-2048 verification on every reset. This adds boot latency before the application starts.

### 4. Create and Sign the Firmware Package
Build your application firmware normally, then use the standalone Firmware Signing Tool to wrap your application in the signed package format. 

```sh
# Example usage of the Python signing tool
python3 Tool/firmware_signing_tool/sign.py \
    --app application.bin \
    --key private_key.pem \
    --out application_signed.bin
```
The signature covers only the application binary, but is packaged with metadata headers into `application_signed.bin`.

### 5. Flash the Signed Package using the Flashing Tool
Use the PC Flashing Tool to upload the package to the target. 

The secure Release bootloader will execute the following security checks:
1. Validates the signature length (256 bytes) and enabled flag during `DOWNLOAD_START`.
2. Computes the SHA-256 hash incrementally directly from the received `DATA` blocks, writing to flash at the same time.
3. Finalizes the hash at `DOWNLOAD_END`.
4. Verifies the SHA-256 digest against the provided RSA signature.
5. If valid, writes the Valid Application Marker to flash.


### Release Without Secure Boot

For a Release build without boot-time RSA enforcement, use:

```sh
make release SECURE_BOOT=OFF
```

This does not require a public key and does not verify the application signature before jumping.
Use this only when secure boot is intentionally disabled.
