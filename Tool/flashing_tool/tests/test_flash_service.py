import pytest
import struct
from transport.fake_transport import FakeTransport
from protocol.protocol_client import ProtocolClient
from protocol.commands import Command
from protocol.frame import encode_frame
from protocol.errors import ErrorCode
from firmware.firmware_image import FirmwareImage
from services.flash_service import FlashService

def test_flash_happy_path():
    transport = FakeTransport()
    client = ProtocolClient(transport)
    service = FlashService(client)
    
    # Prepare mock responses in transport.to_read
    
    # 1. HELLO_RESPONSE
    # Bootloader protocol v1, version 1.2.3, caps 0, max_payload 256, app_start 0x08008000, app_size 0x78000
    hello_payload = struct.pack("<BBBB I H I I", 1, 1, 2, 3, 0, 256, 0x08008000, 0x78000)
    transport.to_read += encode_frame(Command.HELLO_RESPONSE, 1, hello_payload)
    
    # 2. START_SESSION_RESPONSE
    transport.to_read += encode_frame(Command.START_SESSION_RESPONSE, 2, bytes([ErrorCode.OK]))
    
    # 3. ERASE_RESPONSE
    transport.to_read += encode_frame(Command.ERASE_RESPONSE, 3, bytes([ErrorCode.OK]))
    
    # 4. DOWNLOAD_START_RESPONSE
    transport.to_read += encode_frame(Command.DOWNLOAD_START_RESPONSE, 4, bytes([ErrorCode.OK]))
    
    # 5. DATA_RESPONSE (for 10 bytes firmware, chunk size 246, so only 1 chunk)
    transport.to_read += encode_frame(Command.DATA_RESPONSE, 5, bytes([ErrorCode.OK]) + struct.pack("<I", 0))
    
    # 6. DOWNLOAD_END_RESPONSE
    transport.to_read += encode_frame(Command.DOWNLOAD_END_RESPONSE, 6, bytes([ErrorCode.OK]))
    
    transport.open()
    
    fw = FirmwareImage(b"0123456789")
    
    progress_calls = []
    def progress(current, total):
        progress_calls.append((current, total))
        
    service.flash_firmware(fw, progress_callback=progress)
    
    assert len(progress_calls) == 1
    assert progress_calls[0] == (10, 10)
    assert transport.is_open()
