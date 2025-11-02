# CRC Verification Tool

Python script để verify các thuật toán CRC sử dụng trong bootloader.

## Thuật toán được implement

### CRC8
- **Initial value:** 0x00
- **Polynomial:** 0x07
- **XOR Out:** 0x00
- **Reflect In/Out:** False

### CRC16 (CRC-CCITT)
- **Initial value:** 0xFFFF
- **Polynomial:** 0x1021
- **XOR Out:** 0x0000
- **Reflect In/Out:** False

### CRC32
- **Initial value:** 0xFFFFFFFF
- **Polynomial:** 0xEDB88320 (reversed)
- **XOR Out:** 0xFFFFFFFF
- **Reflect In/Out:** True

## Sử dụng

### Chạy test vectors
```bash
python crc_verify.py
```

### Import vào code khác
```python
from crc_verify import CRC8, CRC16, CRC32

# Tính CRC8
data = b"Hello"
crc8_value = CRC8.calculate(data)
print(f"CRC8: 0x{crc8_value:02X}")

# Tính CRC16
crc16_value = CRC16.calculate(data)
print(f"CRC16: 0x{crc16_value:04X}")

# Tính CRC32
crc32_value = CRC32.calculate(data)
print(f"CRC32: 0x{crc32_value:08X}")

# Tính CRC incremental
crc = CRC32()
crc.update(b"Hello, ")
crc.update(b"World!")
result = crc.finalize()
print(f"CRC32: 0x{result:08X}")
```

### Tính CRC từ hex string
```python
from crc_verify import calculate_crc_from_hex_string

calculate_crc_from_hex_string("01 02 03 04 05")
# hoặc
calculate_crc_from_hex_string("0102030405")
```

## Output mẫu

```
=============================================================
CRC Algorithm Verification
=============================================================

Test Vector 1:
  Data: b'123456789'
  Length: 9 bytes
  CRC8:  0xF4 (244)
  CRC16: 0x29B1 (10673)
  CRC32: 0xCBF43926 (3421780262)

✓ Incremental calculation matches one-shot calculation!
```
