import pytest
import struct
from firmware.firmware_image import (
    APP_SECTION_ID,
    SIGNATURE_SECTION_ID,
    SIGNATURE_SIZE,
    FirmwareImage,
)
from firmware.checksum import calculate_crc32

def create_test_package(app_data: bytes, signature: bytes) -> bytes:
    app_crc32 = calculate_crc32(app_data)
    sig_crc32 = calculate_crc32(signature)
    app_header = struct.pack("<HII", APP_SECTION_ID, len(app_data), app_crc32)
    sig_header = struct.pack("<HII", SIGNATURE_SECTION_ID, len(signature), sig_crc32)
    return app_header + app_data + sig_header + signature

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

def test_firmware_rejects_non_bin(tmp_path):
    hex_file = tmp_path / "test.hex"
    hex_file.write_text(":00000001FF")
    with pytest.raises(ValueError, match="Only .bin files are supported"):
        FirmwareImage.from_file(str(hex_file))

def test_firmware_rejects_raw_bin(tmp_path):
    bin_content = b"\x05\x06\x07\x08"
    bin_file = tmp_path / "test.bin"
    bin_file.write_bytes(bin_content)
    with pytest.raises(ValueError, match="Invalid firmware structure"):
        FirmwareImage.from_file(str(bin_file))

def test_signed_package_loading(tmp_path):
    app_data = b"application"
    signature = bytes(range(SIGNATURE_SIZE))
    package_data = create_test_package(app_data, signature)
    package_file = tmp_path / "app_signed_package.bin"
    package_file.write_bytes(package_data)

    parsed = FirmwareImage.from_file(str(package_file))

    assert parsed.data == app_data
    assert parsed.size == len(app_data)
    assert parsed.crc32 == calculate_crc32(app_data)
    assert parsed.signature == signature
    assert parsed.signature_crc32 == calculate_crc32(signature)

def test_signed_package_rejects_bad_crc(tmp_path):
    app_data = b"application"
    signature = bytes(range(SIGNATURE_SIZE))
    package = bytearray(create_test_package(app_data, signature))
    package[12] ^= 0x01 # Corrupt app data
    package_file = tmp_path / "bad_package.bin"
    package_file.write_bytes(bytes(package))

    with pytest.raises(ValueError, match="CRC32 is invalid"):
        FirmwareImage.from_file(str(package_file))

def test_signed_package_rejects_truncated(tmp_path):
    app_data = b"application"
    signature = bytes(range(SIGNATURE_SIZE))
    package = create_test_package(app_data, signature)
    package_file = tmp_path / "truncated.bin"
    package_file.write_bytes(package[:-1])

    with pytest.raises(ValueError, match="Invalid firmware structure"):
        FirmwareImage.from_file(str(package_file))
