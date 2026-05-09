from typing import Iterator, Optional
import os
import struct
from intelhex import IntelHex
from .checksum import calculate_crc32
from .signer import FirmwareSigner

APP_SECTION_ID = 0xA501
SIGNATURE_SECTION_ID = 0x5A02
SECTION_HEADER_SIZE = 10
SIGNATURE_SIZE = 256
SECTION_HEADER_FORMAT = "<HII"

class FirmwareImage:
    def __init__(
        self,
        data: bytes,
        signer: Optional[FirmwareSigner] = None,
        base_address: Optional[int] = None,
        signature: Optional[bytes] = None,
    ):
        self.data = data
        self.size = len(data)
        self.crc32 = calculate_crc32(data)
        self.signature = signature
        self.base_address = base_address
        if signer:
            self.signature = signer.sign(data)
        self.signature_crc32 = calculate_crc32(self.signature) if self.signature else None

    @classmethod
    def from_file(cls, file_path: str, signer: Optional[FirmwareSigner] = None) -> 'FirmwareImage':
        _, ext = os.path.splitext(file_path.lower())

        if ext in ('.hex', '.ihex', '.ihx'):
            ih = IntelHex(file_path)
            # convert to binary data
            # tobinarray() with no arguments returns data from minaddr() to maxaddr()
            data = ih.tobinarray()
            return cls(bytes(data), signer, base_address=ih.minaddr())
        else:
            with open(file_path, 'rb') as f:
                data = f.read()
            package = cls._try_parse_signed_package(bytes(data))
            if package is not None:
                app_data, signature = package
                return cls(app_data, signer, signature=signature)
            return cls(bytes(data), signer)

    @staticmethod
    def _read_section_header(data: bytes, offset: int) -> tuple[int, int, int]:
        if len(data) < offset + SECTION_HEADER_SIZE:
            raise ValueError("Firmware package header is truncated")
        return struct.unpack_from(SECTION_HEADER_FORMAT, data, offset)

    @classmethod
    def _try_parse_signed_package(cls, data: bytes) -> Optional[tuple[bytes, bytes]]:
        if len(data) < ((2 * SECTION_HEADER_SIZE) + SIGNATURE_SIZE):
            return None

        app_id, app_size, app_crc32 = cls._read_section_header(data, 0)
        if app_id != APP_SECTION_ID:
            return None

        sig_header_offset = SECTION_HEADER_SIZE + app_size
        sig_offset = sig_header_offset + SECTION_HEADER_SIZE
        expected_size = sig_offset + SIGNATURE_SIZE
        if len(data) != expected_size:
            raise ValueError("Firmware package size does not match section headers")

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

    def to_signed_package(
        self,
        app_id: int = APP_SECTION_ID,
        signature_id: int = SIGNATURE_SECTION_ID,
    ) -> bytes:
        if self.signature is None:
            raise ValueError("Firmware image has no signature")
        if len(self.signature) != SIGNATURE_SIZE:
            raise ValueError("Firmware signature size is invalid")
        if not 0 <= app_id <= 0xFFFF:
            raise ValueError("Application section ID is out of range")
        if not 0 <= signature_id <= 0xFFFF:
            raise ValueError("Signature section ID is out of range")

        signature_crc32 = calculate_crc32(self.signature)
        app_header = struct.pack(SECTION_HEADER_FORMAT, app_id, self.size, self.crc32)
        sig_header = struct.pack(SECTION_HEADER_FORMAT, signature_id, len(self.signature), signature_crc32)
        return app_header + self.data + sig_header + self.signature

    def get_chunks(self, max_data_per_frame: int) -> Iterator[tuple[int, int, bytes]]:
        """
        Yields (block_index, offset, data_chunk)
        """
        offset = 0
        block_index = 0
        while offset < self.size:
            chunk = self.data[offset : offset + max_data_per_frame]
            yield block_index, offset, chunk
            offset += len(chunk)
            block_index += 1
