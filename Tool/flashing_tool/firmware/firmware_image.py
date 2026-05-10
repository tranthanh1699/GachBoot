from typing import Iterator, Optional
import os
import struct
from .checksum import calculate_crc32

APP_SECTION_ID = 0xA501
SIGNATURE_SECTION_ID = 0x5A02
SECTION_HEADER_SIZE = 10
SIGNATURE_SIZE = 256
SECTION_HEADER_FORMAT = "<HII"

class FirmwareImage:
    def __init__(
        self,
        data: bytes,
        base_address: Optional[int] = None,
        signature: Optional[bytes] = None,
        package_data: Optional[bytes] = None,
    ):
        self.data = data
        self.size = len(data)
        self.crc32 = calculate_crc32(data)
        self.signature = signature
        self.base_address = base_address
        self.signature_crc32 = calculate_crc32(self.signature) if self.signature else None
        self.package_data = package_data
        self.package_size = len(package_data) if package_data is not None else len(data)
        self.package_crc32 = calculate_crc32(package_data) if package_data is not None else self.crc32

    @classmethod
    def from_file(cls, file_path: str) -> 'FirmwareImage':
        _, ext = os.path.splitext(file_path.lower())

        if ext != '.bin':
            raise ValueError("Only .bin files are supported. Firmware must be a signed package.")

        with open(file_path, 'rb') as f:
            data = f.read()

        package = cls._try_parse_signed_package(bytes(data))
        if package is None:
            raise ValueError("Invalid firmware structure. File must be a signed package [Header App] + [App] + [Header Sig] + [Sig].")

        app_data, signature = package
        return cls(app_data, signature=signature, package_data=bytes(data))

    @staticmethod
    def _read_section_header(data: bytes, offset: int) -> tuple[int, int, int]:
        if len(data) < offset + SECTION_HEADER_SIZE:
            raise ValueError("Firmware package header is truncated")
        return struct.unpack_from(SECTION_HEADER_FORMAT, data, offset)

    @classmethod
    def _try_parse_signed_package(cls, data: bytes) -> Optional[tuple[bytes, bytes]]:
        if len(data) < ((2 * SECTION_HEADER_SIZE) + SIGNATURE_SIZE):
            return None

        try:
            app_id, app_size, app_crc32 = cls._read_section_header(data, 0)
            if app_id != APP_SECTION_ID:
                return None

            sig_header_offset = SECTION_HEADER_SIZE + app_size
            sig_offset = sig_header_offset + SECTION_HEADER_SIZE
            expected_size = sig_offset + SIGNATURE_SIZE

            if len(data) != expected_size:
                return None

            app_data = data[SECTION_HEADER_SIZE:sig_header_offset]
            if calculate_crc32(app_data) != app_crc32:
                raise ValueError("Firmware package application CRC32 is invalid")

            sig_id, sig_size, sig_crc32 = cls._read_section_header(data, sig_header_offset)
            if sig_id != SIGNATURE_SECTION_ID:
                raise ValueError("Firmware package signature section ID is invalid")
            if sig_size != SIGNATURE_SIZE:
                raise ValueError("Firmware package signature size is invalid")

            signature = data[sig_offset:expected_size]
            if calculate_crc32(signature) != sig_crc32:
                raise ValueError("Firmware package signature CRC32 is invalid")

            return app_data, signature
        except struct.error:
            return None

    def to_signed_package(self) -> bytes:
        if not self.signature:
            raise ValueError("Firmware is not signed")
        app_header = struct.pack(SECTION_HEADER_FORMAT, APP_SECTION_ID, self.size, self.crc32)
        sig_header = struct.pack(SECTION_HEADER_FORMAT, SIGNATURE_SECTION_ID, SIGNATURE_SIZE, self.signature_crc32)
        return app_header + self.data + sig_header + self.signature

    def get_chunks(self, max_data_per_frame: int) -> Iterator[tuple[int, int, bytes]]:
        """
        Yields (block_index, offset, data_chunk)
        """
        source = self.package_data if self.package_data is not None else self.data
        offset = 0
        block_index = 0
        while offset < len(source):
            chunk = source[offset : offset + max_data_per_frame]
            yield block_index, offset, chunk
            offset += len(chunk)
            block_index += 1
