# GachBoot Firmware Signing Tool

A Python-based command-line tool for signing application firmware using RSA-2048 (SHA-256) and packaging it into a format that the GachBoot STM32 bootloader can verify and flash.

## Features
- RSA-2048 PKCS#1 v1.5 SHA-256 firmware signing.
- Custom binary packaging with headers for application and signature.
- CRC32 verification for all sections.
- Inspection mode for validating signed packages.
- Deterministic little-endian encoding.

## Installation

The tool requires Python 3.6+ and the `cryptography` library.

```bash
# Recommended: Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install cryptography
```

## Usage Examples

### 1. Generate an RSA Key Pair (using OpenSSL)
```bash
openssl genrsa -F4 -out key.pem 2048
```

### 2. Sign and Package Firmware
```bash
python3 firmware_sign_tool.py \
  --input app.bin \
  --private-key key.pem \
  --output app_signed_package.bin \
  --verbose
```

### 3. Inspect and Validate a Package
```bash
python3 firmware_sign_tool.py --inspect app_signed_package.bin
```

### 4. Custom Section IDs
```bash
python3 firmware_sign_tool.py \
  --input app.bin \
  --private-key key.pem \
  --output app_signed_package.bin \
  --app-id 0x1234 \
  --signature-id 0x5678
```

## Binary Package Layout

The tool generates a single binary file with the following structure:

| Offset | Size | Name | Description |
| :--- | :--- | :--- | :--- |
| 0 | 2 | App ID | 0xA501 (Little-Endian) |
| 2 | 4 | App Size | Application binary size (N) |
| 6 | 4 | App CRC32 | CRC32 of application binary |
| 10 | N | App Binary | Raw application data |
| 10+N | 2 | Sig ID | 0x5A02 (Little-Endian) |
| 12+N | 4 | Sig Size | Signature size (256) |
| 16+N | 4 | Sig CRC32 | CRC32 of signature |
| 20+N | 256 | Signature | RSA-2048 Signature |

## Makefile Integration Example

```makefile
# Variables
FW_TOOL = python3 Tool/firmware_signing_tool/firmware_sign_tool.py
KEY = keys/private_key.pem
INPUT = build/application.bin
OUTPUT = build/application_signed.bin

# Sign target
sign: $(INPUT)
	@echo "Signing firmware..."
	$(FW_TOOL) --input $(INPUT) --private-key $(KEY) --output $(OUTPUT) --verbose

# Inspect target
inspect: $(OUTPUT)
	$(FW_TOOL) --inspect $(OUTPUT)
```

## Example Bootloader Parsing (C Pseudocode)

```c
#include <stdint.h>
#include <string.h>

typedef struct {
    uint16_t id;
    uint32_t size;
    uint32_t crc32;
} __attribute__((packed)) SectionHeader_t;

#define APP_SECTION_ID       0xA501
#define SIGNATURE_SECTION_ID 0x5A02

bool process_signed_package(uint8_t *package_buffer, uint32_t total_size) {
    SectionHeader_t *app_header = (SectionHeader_t *)package_buffer;
    
    // 1. Validate App Header
    if (app_header->id != APP_SECTION_ID) return false;
    
    uint8_t *app_binary = package_buffer + sizeof(SectionHeader_t);
    uint32_t calculated_app_crc = HAL_CRC_Calculate(&hcrc, (uint32_t *)app_binary, app_header->size);
    if (calculated_app_crc != app_header->crc32) return false;
    
    // 2. Validate Signature Header
    SectionHeader_t *sig_header = (SectionHeader_t *)(app_binary + app_header->size);
    if (sig_header->id != SIGNATURE_SECTION_ID) return false;
    if (sig_header->size != 256) return false;
    
    uint8_t *signature = (uint8_t *)sig_header + sizeof(SectionHeader_t);
    uint32_t calculated_sig_crc = HAL_CRC_Calculate(&hcrc, (uint32_t *)signature, sig_header->size);
    if (calculated_sig_crc != sig_header->crc32) return false;
    
    // 3. RSA Verification (using target library like mbedTLS or custom RSA-2048)
    // SHA256(app_binary) -> digest
    // Verify(digest, signature, public_key)
    if (rsa_verify_sha256(app_binary, app_header->size, signature, public_key) != SUCCESS) {
        return false;
    }
    
    return true; // Package is valid
}
```
