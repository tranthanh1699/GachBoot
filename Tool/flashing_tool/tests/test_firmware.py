import pytest
import os
import struct
from firmware.firmware_image import (
    APP_SECTION_ID,
    SIGNATURE_SECTION_ID,
    SIGNATURE_SIZE,
    FirmwareImage,
)
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
    assert fw.base_address == 0x08000000

def test_firmware_bin_loading(tmp_path):
    bin_content = b"\x05\x06\x07\x08"
    bin_file = tmp_path / "test.bin"
    bin_file.write_bytes(bin_content)

    fw = FirmwareImage.from_file(str(bin_file))
    assert fw.data == bin_content
    assert fw.size == 4
    assert fw.base_address is None

def test_signed_package_round_trip(tmp_path):
    app_data = b"application"
    signature = bytes(range(256))
    package_file = tmp_path / "app_signed_package.bin"
    fw = FirmwareImage(app_data, signature=signature)

    package_file.write_bytes(fw.to_signed_package())
    parsed = FirmwareImage.from_file(str(package_file))

    assert parsed.data == app_data
    assert parsed.size == len(app_data)
    assert parsed.crc32 == calculate_crc32(app_data)
    assert parsed.signature == signature
    assert parsed.signature_crc32 == calculate_crc32(signature)

def test_signed_package_rejects_bad_crc(tmp_path):
    app_data = b"application"
    signature = bytes(range(SIGNATURE_SIZE))
    package = bytearray(FirmwareImage(app_data, signature=signature).to_signed_package())
    package[12] ^= 0x01
    package_file = tmp_path / "bad_package.bin"
    package_file.write_bytes(bytes(package))

    with pytest.raises(ValueError):
        FirmwareImage.from_file(str(package_file))

def test_signed_package_header_layout():
    app_data = b"app"
    signature = bytes(range(SIGNATURE_SIZE))
    package = FirmwareImage(app_data, signature=signature).to_signed_package()

    app_id, app_size, app_crc32 = struct.unpack_from("<HII", package, 0)
    sig_offset = 10 + len(app_data)
    sig_id, sig_size, sig_crc32 = struct.unpack_from("<HII", package, sig_offset)

    assert app_id == APP_SECTION_ID
    assert app_size == len(app_data)
    assert app_crc32 == calculate_crc32(app_data)
    assert sig_id == SIGNATURE_SECTION_ID
    assert sig_size == SIGNATURE_SIZE
    assert sig_crc32 == calculate_crc32(signature)
