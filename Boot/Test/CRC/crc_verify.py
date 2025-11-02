"""
CRC Verification Script
This script implements the same CRC algorithms as the embedded C code
to verify correctness of CRC calculations.

Algorithms:
- CRC8:  Init=0x00, Poly=0x07, XorOut=0x00, RefIn=False, RefOut=False
- CRC16: Init=0xFFFF, Poly=0x1021 (CRC-CCITT), XorOut=0x0000, RefIn=False, RefOut=False  
- CRC32: Init=0xFFFFFFFF, Poly=0xEDB88320 (reversed), XorOut=0xFFFFFFFF, RefIn=True, RefOut=True
"""


class CRC8:
    """CRC8 implementation matching the embedded C code"""
    
    def __init__(self):
        self.crc = 0x00
    
    def update(self, data: bytes):
        """Update CRC with new data"""
        crc = self.crc
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x07) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        self.crc = crc
    
    def finalize(self) -> int:
        """Get the final CRC value"""
        return self.crc
    
    @staticmethod
    def calculate(data: bytes) -> int:
        """Calculate CRC8 in one step"""
        crc8 = CRC8()
        crc8.update(data)
        return crc8.finalize()


class CRC16:
    """CRC16-CCITT implementation matching the embedded C code"""
    
    def __init__(self):
        self.crc = 0xFFFF
    
    def update(self, data: bytes):
        """Update CRC with new data"""
        crc = self.crc
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ 0x1021) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
        self.crc = crc
    
    def finalize(self) -> int:
        """Get the final CRC value"""
        return self.crc
    
    @staticmethod
    def calculate(data: bytes) -> int:
        """Calculate CRC16 in one step"""
        crc16 = CRC16()
        crc16.update(data)
        return crc16.finalize()


class CRC32:
    """CRC32 implementation matching the embedded C code"""
    
    def __init__(self):
        self.crc = 0xFFFFFFFF
    
    def update(self, data: bytes):
        """Update CRC with new data"""
        crc = self.crc
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xEDB88320
                else:
                    crc = crc >> 1
        self.crc = crc
    
    def finalize(self) -> int:
        """Get the final CRC value"""
        return (~self.crc) & 0xFFFFFFFF
    
    @staticmethod
    def calculate(data: bytes) -> int:
        """Calculate CRC32 in one step"""
        crc32 = CRC32()
        crc32.update(data)
        return crc32.finalize()


def test_crc_algorithms():
    """Test CRC algorithms with various test vectors"""
    
    print("=" * 60)
    print("CRC Algorithm Verification")
    print("=" * 60)
    
    # Test data
    test_vectors = [
        b"123456789",           # Standard test vector
        b"Hello, World!",       # ASCII string
        b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09",  # Binary data
        b"",                    # Empty data
        b"\xFF" * 10,           # All 0xFF
        b"A" * 100,             # Repeated character
    ]
    
    for i, data in enumerate(test_vectors):
        print(f"\nTest Vector {i + 1}:")
        print(f"  Data: {data[:20]}{'...' if len(data) > 20 else ''}")
        print(f"  Length: {len(data)} bytes")
        
        # CRC8
        crc8 = CRC8.calculate(data)
        print(f"  CRC8:  0x{crc8:02X} ({crc8})")
        
        # CRC16
        crc16 = CRC16.calculate(data)
        print(f"  CRC16: 0x{crc16:04X} ({crc16})")
        
        # CRC32
        crc32 = CRC32.calculate(data)
        print(f"  CRC32: 0x{crc32:08X} ({crc32})")
    
    # Test incremental update
    print("\n" + "=" * 60)
    print("Testing Incremental Update")
    print("=" * 60)
    
    full_data = b"The quick brown fox jumps over the lazy dog"
    
    # Calculate in one go
    crc8_full = CRC8.calculate(full_data)
    crc16_full = CRC16.calculate(full_data)
    crc32_full = CRC32.calculate(full_data)
    
    # Calculate incrementally
    crc8_inc = CRC8()
    crc16_inc = CRC16()
    crc32_inc = CRC32()
    
    # Split into chunks
    chunk_size = 10
    for i in range(0, len(full_data), chunk_size):
        chunk = full_data[i:i + chunk_size]
        crc8_inc.update(chunk)
        crc16_inc.update(chunk)
        crc32_inc.update(chunk)
    
    print(f"\nFull data: {full_data}")
    print(f"\nOne-shot calculation:")
    print(f"  CRC8:  0x{crc8_full:02X}")
    print(f"  CRC16: 0x{crc16_full:04X}")
    print(f"  CRC32: 0x{crc32_full:08X}")
    
    print(f"\nIncremental calculation ({chunk_size}-byte chunks):")
    print(f"  CRC8:  0x{crc8_inc.finalize():02X}")
    print(f"  CRC16: 0x{crc16_inc.finalize():04X}")
    print(f"  CRC32: 0x{crc32_inc.finalize():08X}")
    
    # Verify they match
    assert crc8_full == crc8_inc.finalize(), "CRC8 mismatch!"
    assert crc16_full == crc16_inc.finalize(), "CRC16 mismatch!"
    assert crc32_full == crc32_inc.finalize(), "CRC32 mismatch!"
    
    print("\n✓ Incremental calculation matches one-shot calculation!")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


def calculate_crc_from_hex_string(hex_string: str):
    """
    Calculate CRC from hex string input
    Example: "01 02 03 04 05" or "0102030405"
    """
    # Remove spaces and convert to bytes
    hex_string = hex_string.replace(" ", "").replace("0x", "")
    data = bytes.fromhex(hex_string)
    
    print(f"\nInput hex: {hex_string}")
    print(f"Data bytes: {' '.join(f'{b:02X}' for b in data)}")
    print(f"CRC8:  0x{CRC8.calculate(data):02X}")
    print(f"CRC16: 0x{CRC16.calculate(data):04X}")
    print(f"CRC32: 0x{CRC32.calculate(data):08X}")


if __name__ == "__main__":
    test_crc_algorithms()
    
    # Example: Calculate CRC for custom hex data
    print("\n\n" + "=" * 60)
    print("Custom Hex Data Example")
    print("=" * 60)
    calculate_crc_from_hex_string("01 02 03 04 05 06 07 08 09 0A")
