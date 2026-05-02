from typing import Iterator, Optional
import os
from intelhex import IntelHex
from .checksum import calculate_crc32
from .signer import FirmwareSigner

class FirmwareImage:
    def __init__(self, data: bytes, signer: Optional[FirmwareSigner] = None):
        self.data = data
        self.size = len(data)
        self.crc32 = calculate_crc32(data)
        self.signature = None
        if signer:
            self.signature = signer.sign(data)

    @classmethod
    def from_file(cls, file_path: str, signer: Optional[FirmwareSigner] = None) -> 'FirmwareImage':
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.hex':
            ih = IntelHex(file_path)
            # convert to binary data
            # Note: to_binarray() returns a bytearray of the used range
            data = ih.tobinarray()
        else:
            with open(file_path, 'rb') as f:
                data = f.read()
                
        return cls(bytes(data), signer)

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
