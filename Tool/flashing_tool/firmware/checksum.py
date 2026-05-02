import binascii

def calculate_crc32(data: bytes) -> int:
    """Calculate CRC32 of data. Returns result as uint32."""
    return binascii.crc32(data) & 0xFFFFFFFF
