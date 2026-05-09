import struct
import time
from typing import Callable, Optional
from protocol.commands import Command
from protocol.errors import ErrorCode
from protocol.protocol_client import ProtocolClient, ProtocolError
from firmware.firmware_image import FirmwareImage

DATA_HEADER_SIZE = 10
FLASH_WRITE_ALIGN = 32

class BootloaderInfo:
    def __init__(self, payload: bytes):
        # Expected length 18
        (self.protocol_version, self.major, self.minor, self.patch, 
         self.capabilities, self.max_payload, self.app_start, self.app_max_size) = \
            struct.unpack("<BBBB I H I I", payload)

class FlashService:
    def __init__(self, client: ProtocolClient):
        self.client = client
        self.boot_info: Optional[BootloaderInfo] = None

    def hello(self) -> BootloaderInfo:
        # Tool Protocol Version: 1 byte, Tool Capability Flags: 4 bytes
        payload = struct.pack("<B I", 1, 0)
        rsp = self.client.request_response(Command.HELLO, payload)
        self.boot_info = BootloaderInfo(rsp.payload)
        return self.boot_info

    def start_session(self):
        rsp = self.client.request_response(Command.START_SESSION)
        status = rsp.payload[0]
        if status != ErrorCode.OK:
            raise ProtocolError(Command.START_SESSION, ErrorCode(status))

    def erase(self):
        rsp = self.client.request_response(Command.ERASE)
        status = rsp.payload[0]
        if status != ErrorCode.OK:
            raise ProtocolError(Command.ERASE, ErrorCode(status))

    def download_start(self, firmware: FirmwareImage):
        if not self.boot_info:
            raise ValueError("Must call hello() before download_start()")
        
        # Use firmware's base address if available (e.g. from HEX file),
        # otherwise use the bootloader's default app_start address.
        target_address = firmware.base_address if firmware.base_address is not None else self.boot_info.app_start
        
        sig_enabled = 1 if firmware.signature else 0
        sig_len = len(firmware.signature) if firmware.signature else 0
        
        # Firmware size: 4, CRC32: 4, Target: 4, SigEnabled: 1, SigLen: 2
        payload = struct.pack("<I I I B H", 
                              firmware.size, 
                              firmware.crc32, 
                              target_address,
                              sig_enabled,
                              sig_len)
        
        if firmware.signature:
            payload += firmware.signature
            
        rsp = self.client.request_response(Command.DOWNLOAD_START, payload)
        status = rsp.payload[0]
        if status != ErrorCode.OK:
            raise ProtocolError(Command.DOWNLOAD_START, ErrorCode(status))

    def send_data(self, block_index: int, offset: int, data: bytes):
        # Block index: 4, Offset: 4, Length: 2, Data: N
        header = struct.pack("<I I H", block_index, offset, len(data))
        payload = header + data
        rsp = self.client.request_response(Command.DATA, payload)
        status = rsp.payload[0]
        ack_index = struct.unpack("<I", rsp.payload[1:5])[0]
        
        if status != ErrorCode.OK:
            raise ProtocolError(Command.DATA, ErrorCode(status))
        if ack_index != block_index:
            raise ValueError(f"Block index mismatch: sent {block_index}, acked {ack_index}")

    def download_end(self):
        rsp = self.client.request_response(Command.DOWNLOAD_END)
        status = rsp.payload[0]
        if status != ErrorCode.OK:
            raise ProtocolError(Command.DOWNLOAD_END, ErrorCode(status))

    def reset(self):
        rsp = self.client.request_response(Command.RESET)
        status = rsp.payload[0]
        if status != ErrorCode.OK:
            raise ProtocolError(Command.RESET, ErrorCode(status))

    def abort(self):
        try:
            self.client.request_response(Command.ABORT)
        except Exception:
            # Best effort
            pass

    def flash_firmware(self, firmware: FirmwareImage, progress_callback: Optional[Callable[[int, int], None]] = None):
        try:
            self.hello()
            self.start_session()
            self.erase()
            self.download_start(firmware)
            
            # Non-final DATA blocks must preserve STM32H7 flash-word alignment.
            max_data_per_frame = self.boot_info.max_payload - DATA_HEADER_SIZE
            max_chunk = max_data_per_frame - (max_data_per_frame % FLASH_WRITE_ALIGN)
            if max_chunk <= 0:
                raise ValueError("Bootloader max payload is too small for aligned DATA frames")
            
            for block_index, offset, chunk in firmware.get_chunks(max_chunk):
                self.send_data(block_index, offset, chunk)
                if progress_callback:
                    progress_callback(offset + len(chunk), firmware.size)
            
            self.download_end()
            self.reset()
        except Exception as e:
            self.abort()
            raise e
