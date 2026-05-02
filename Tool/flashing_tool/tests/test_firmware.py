import pytest
from firmware.firmware_image import FirmwareImage
from firmware.checksum import calculate_crc32

def test_crc32():
    data = b"\x01\x02\x03\x04"
    # Result for 0x01020304 in some calculators might differ by endianness, 
    # but zlib/binascii.crc32 is standard.
    import binascii
    assert calculate_crc32(data) == binascii.crc32(data) & 0xFFFFFFFF

def test_firmware_chunking():
    data = b"ABCDEFGHIJ" # 10 bytes
    fw = FirmwareImage(data)
    
    # Chunk size 3
    chunks = list(fw.get_chunks(3))
    assert len(chunks) == 4
    assert chunks[0] == (0, 0, b"ABC")
    assert chunks[1] == (1, 3, b"DEF")
    assert chunks[2] == (2, 6, b"GHI")
    assert chunks[3] == (3, 9, b"J")

def test_firmware_metadata():
    data = b"Hello"
    fw = FirmwareImage(data)
    assert fw.size == 5
    assert fw.crc32 == calculate_crc32(data)
