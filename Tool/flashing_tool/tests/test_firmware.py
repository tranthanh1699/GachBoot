import pytest
import os
from firmware.firmware_image import FirmwareImage
from firmware.checksum import calculate_crc32

def test_crc32():
    data = b"\x01\x02\x03\x04"
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

def test_firmware_hex_loading(tmp_path):
    # Create a simple Intel HEX file
    # :020000040800F2 (Extended Linear Address: 0x08000000)
    # :0400000001020304F2 (Data: 0x01 0x02 0x03 0x04 at offset 0, Checksum: 100 - (4+0+0+0+1+2+3+4) = F2)
    # :00000001FF (End of File)
    hex_content = (
        ":020000040800F2\n"
        ":0400000001020304F2\n"
        ":00000001FF\n"
    )
    hex_file = tmp_path / "test.hex"
    hex_file.write_text(hex_content)
    
    fw = FirmwareImage.from_file(str(hex_file))
    # intelhex tobinarray returns only the bytes present in the hex
    assert fw.data == b"\x01\x02\x03\x04"
    assert fw.size == 4
