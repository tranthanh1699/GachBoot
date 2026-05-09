# Task: Create Python firmware signing tool for STM32 bootloader package

Read and analyze this repository first:

https://github.com/jhallen/rsa-verify/tree/master?tab=readme-ov-file

The target-side STM32 bootloader will use RSA-2048 SHA-256 verification compatible with the algorithm/style from that repository.

Now create a host-side Python 3 command-line tool that signs application firmware using a private key and generates one packaged binary file that the STM32 bootloader can parse and flash.

---

# Language requirement

Implement the tool in Python 3 only.

Do NOT implement the tool in C.

The tool runs on Linux PC/build machine, not on STM32 target.

Use Python package:

```bash
pip install cryptography
```

---

# Goal

Create a command-line tool:

```bash
firmware_sign_tool \
  --input app.bin \
  --private-key key.pem \
  --output app_signed_package.bin
```

The tool shall generate a binary package with this exact layout:

```text
[Header App] + [App Binary] + [Header Signature] + [Signature]
```

---

# Package layout

## Header App

```c
typedef struct
{
    uint16_t id;
    uint32_t size;
    uint32_t crc32;
} AppHeaderType;
```

Meaning:

```text
id     : 2-byte application section ID
size   : 4-byte application binary size
crc32  : CRC32 of application binary only
```

---

## App Binary

Raw application binary from `--input`.

---

## Header Signature

```c
typedef struct
{
    uint16_t id;
    uint32_t size;
    uint32_t crc32;
} SignatureHeaderType;
```

Meaning:

```text
id     : 2-byte signature section ID
size   : signature size in bytes
crc32  : CRC32 of signature only
```

---

## Signature

RSA-2048 PKCS#1 v1.5 SHA-256 signature.

Signature size:

```text
256 bytes
```

---

# Binary encoding rules

All integers must use fixed little-endian encoding:

```text
uint16_t -> little-endian 2 bytes
uint32_t -> little-endian 4 bytes
```

Do NOT rely on native struct packing.

Write deterministic binary serialization explicitly.

Final binary layout:

```text
10 bytes AppHeader
N bytes  App Binary
10 bytes SignatureHeader
256 bytes Signature
```

Because:

```text
2 + 4 + 4 = 10 bytes header size
```

---

# Section IDs

Default IDs:

```text
APP_SECTION_ID       = 0xA501
SIGNATURE_SECTION_ID = 0x5A02
```

Allow override:

```bash
--app-id 0xA501
--signature-id 0x5A02
```

---

# Signing algorithm

Use:

```text
RSA-2048
SHA-256
PKCS#1 v1.5
```

Equivalent OpenSSL concept:

```bash
openssl dgst -sha256 -sign key.pem -out app.sig app.bin
```

Python signing must use:

```python
private_key.sign(
    app_data,
    padding.PKCS1v15(),
    hashes.SHA256()
)
```

The signature must be compatible with STM32 target-side verification based on:

https://github.com/jhallen/rsa-verify/tree/master?tab=readme-ov-file

---

# CRC32

Implement CRC32 for:

1. application binary only
2. signature only

Use standard Ethernet/ZIP CRC32:

```text
Polynomial: 0x04C11DB7
Reflected polynomial: 0xEDB88320
Initial value: 0xFFFFFFFF
Final XOR: 0xFFFFFFFF
Input reflected: yes
Output reflected: yes
```

---

# Required command-line options

Support:

```bash
--input <app.bin>
--private-key <key.pem>
--output <signed_package.bin>
--app-id <hex-or-decimal>
--signature-id <hex-or-decimal>
--verbose
--inspect <signed_package.bin>
```

Required:

```text
--input
--private-key
--output
```

Optional:

```text
--app-id
--signature-id
--verbose
--inspect
```

---

# Validation requirements

Validate:

- input file exists
- private key exists
- output path writable
- app size > 0
- signature size == 256 bytes
- section IDs fit uint16_t
- sizes fit uint32_t
- CRC32 correctness
- generated package size correctness

On validation failure:
- print clear error
- return non-zero exit code

---

# Inspect mode

Implement:

```bash
firmware_sign_tool --inspect app_signed_package.bin
```

Inspect mode shall print:

```text
App Header:
  ID
  Size
  CRC32

Signature Header:
  ID
  Size
  CRC32

Total package size
Validation result
```

Inspect mode must validate:
- app section ID
- signature section ID
- app CRC32
- signature CRC32
- signature size == 256

---

# Deliverables

Generate:

1. Complete Python source code
2. Linux usage examples
3. Installation command
4. Example package layout
5. Example bootloader parsing pseudocode in C
6. Example Makefile integration
7. Example signing workflow

Keep the implementation concise, clean, and production-oriented.

---

# Example package layout

```text
+----------------------+
| AppHeader            |
+----------------------+
| Application Binary   |
+----------------------+
| SignatureHeader      |
+----------------------+
| RSA2048 Signature    |
+----------------------+
```

---

# Example usage

Generate key:

```bash
openssl genrsa -F4 -out key.pem 2048
```

Generate signed package:

```bash
firmware_sign_tool \
  --input app.bin \
  --private-key key.pem \
  --output app_signed_package.bin \
  --verbose
```

Inspect package:

```bash
firmware_sign_tool \
  --inspect app_signed_package.bin
```

---

# Example bootloader parsing flow

```c
Read AppHeader
Validate AppHeader ID
Validate App CRC32

Read SignatureHeader
Validate SignatureHeader ID
Validate Signature CRC32

Calculate SHA256(app)

Verify RSA signature

If verification OK:
    allow erase/program/activation
Else:
    reject image
```
