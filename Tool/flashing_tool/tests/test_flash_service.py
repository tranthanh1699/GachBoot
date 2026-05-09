import pytest
import struct
from transport.fake_transport import FakeTransport
from protocol.protocol_client import ProtocolClient
from protocol.commands import Command
from protocol.frame import encode_frame
from protocol.errors import ErrorCode
from firmware.firmware_image import FirmwareImage
from services.flash_service import FlashService

def written_commands(transport: FakeTransport) -> list[Command]:
    commands: list[Command] = []
    offset = 0
    while offset < len(transport.written):
        payload_length = struct.unpack("<H", transport.written[offset + 4:offset + 6])[0]
        frame_length = 8 + payload_length
        frame = transport.written[offset:offset + frame_length]
        commands.append(Command(frame[2]))
        offset += frame_length
    return commands

def find_written_frame(transport: FakeTransport, command: Command) -> bytes:
    offset = 0
    while offset < len(transport.written):
        payload_length = struct.unpack("<H", transport.written[offset + 4:offset + 6])[0]
        frame_length = 8 + payload_length
        frame = transport.written[offset:offset + frame_length]
        if frame[2] == command:
            return frame
        offset += frame_length
    raise AssertionError(f"Command {command.name} was not written")

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

    # 7. RESET_RESPONSE
    transport.to_read += encode_frame(Command.RESET_RESPONSE, 7, bytes([ErrorCode.OK]))

    transport.open()

    fw = FirmwareImage(b"0123456789")

    progress_calls = []
    def progress(current, total):
        progress_calls.append((current, total))

    service.flash_firmware(fw, progress_callback=progress)

    assert len(progress_calls) == 1
    assert progress_calls[0] == (10, 10)
    assert written_commands(transport) == [
        Command.HELLO,
        Command.START_SESSION,
        Command.ERASE,
        Command.DOWNLOAD_START,
        Command.DATA,
        Command.DOWNLOAD_END,
        Command.RESET,
    ]
    assert transport.is_open()

def test_flash_uses_aligned_non_final_data_chunks():
    transport = FakeTransport()
    client = ProtocolClient(transport)
    service = FlashService(client)

    hello_payload = struct.pack("<BBBB I H I I", 1, 1, 2, 3, 0, 256, 0x08008000, 0x78000)
    transport.to_read += encode_frame(Command.HELLO_RESPONSE, 1, hello_payload)
    transport.to_read += encode_frame(Command.START_SESSION_RESPONSE, 2, bytes([ErrorCode.OK]))
    transport.to_read += encode_frame(Command.ERASE_RESPONSE, 3, bytes([ErrorCode.OK]))
    transport.to_read += encode_frame(Command.DOWNLOAD_START_RESPONSE, 4, bytes([ErrorCode.OK]))
    transport.to_read += encode_frame(Command.DATA_RESPONSE, 5, bytes([ErrorCode.OK]) + struct.pack("<I", 0))
    transport.to_read += encode_frame(Command.DATA_RESPONSE, 6, bytes([ErrorCode.OK]) + struct.pack("<I", 1))
    transport.to_read += encode_frame(Command.DOWNLOAD_END_RESPONSE, 7, bytes([ErrorCode.OK]))
    transport.to_read += encode_frame(Command.RESET_RESPONSE, 8, bytes([ErrorCode.OK]))
    transport.open()

    fw = FirmwareImage(bytes(range(100)) * 3)
    progress_calls = []

    service.flash_firmware(fw, progress_callback=lambda current, total: progress_calls.append((current, total)))

    assert progress_calls == [(224, 300), (300, 300)]

def test_flash_sends_package_signature_in_download_start(tmp_path):
    transport = FakeTransport()
    client = ProtocolClient(transport)
    service = FlashService(client)

    hello_payload = struct.pack("<BBBB I H I I", 1, 1, 2, 3, 0, 512, 0x08008000, 0x78000)
    transport.to_read += encode_frame(Command.HELLO_RESPONSE, 1, hello_payload)
    transport.to_read += encode_frame(Command.START_SESSION_RESPONSE, 2, bytes([ErrorCode.OK]))
    transport.to_read += encode_frame(Command.ERASE_RESPONSE, 3, bytes([ErrorCode.OK]))
    transport.to_read += encode_frame(Command.DOWNLOAD_START_RESPONSE, 4, bytes([ErrorCode.OK]))
    transport.to_read += encode_frame(Command.DATA_RESPONSE, 5, bytes([ErrorCode.OK]) + struct.pack("<I", 0))
    transport.to_read += encode_frame(Command.DOWNLOAD_END_RESPONSE, 6, bytes([ErrorCode.OK]))
    transport.to_read += encode_frame(Command.RESET_RESPONSE, 7, bytes([ErrorCode.OK]))
    transport.open()

    signature = bytes(range(256))
    package_file = tmp_path / "app_signed_package.bin"
    package_file.write_bytes(FirmwareImage(b"app", signature=signature).to_signed_package())

    fw = FirmwareImage.from_file(str(package_file))
    service.flash_firmware(fw)

    frame = find_written_frame(transport, Command.DOWNLOAD_START)
    payload = frame[6:-2]
    firmware_size, _, _, sig_enabled, sig_len = struct.unpack("<I I I B H", payload[:15])

    assert firmware_size == 3
    assert sig_enabled == 1
    assert sig_len == 256
    assert payload[15:] == signature

def test_protocol_client_uses_command_specific_timeout():
    class TimeoutRecordingTransport(FakeTransport):
        def __init__(self):
            super().__init__()
            self.timeouts = []

        def read(self, size: int, timeout_ms: int) -> bytes:
            self.timeouts.append(timeout_ms)
            return super().read(size, timeout_ms)

        def read_until_sof(self, sof: int, timeout_ms: int) -> bytes:
            self.timeouts.append(timeout_ms)
            return super().read_until_sof(sof, timeout_ms)

    transport = TimeoutRecordingTransport()
    client = ProtocolClient(transport)
    transport.to_read += encode_frame(Command.ERASE_RESPONSE, 1, bytes([ErrorCode.OK]))
    transport.open()

    client.request_response(Command.ERASE)

    assert transport.timeouts == [30000, 30000, 30000]

def test_flash_uses_firmware_base_address():
    transport = FakeTransport()
    client = ProtocolClient(transport)
    service = FlashService(client)

    # app_start in HELLO is 0x08008000
    hello_payload = struct.pack("<BBBB I H I I", 1, 1, 2, 3, 0, 256, 0x08008000, 0x78000)
    transport.to_read += encode_frame(Command.HELLO_RESPONSE, 1, hello_payload)
    transport.to_read += encode_frame(Command.START_SESSION_RESPONSE, 2, bytes([ErrorCode.OK]))
    transport.to_read += encode_frame(Command.ERASE_RESPONSE, 3, bytes([ErrorCode.OK]))
    transport.to_read += encode_frame(Command.DOWNLOAD_START_RESPONSE, 4, bytes([ErrorCode.OK]))
    transport.to_read += encode_frame(Command.DATA_RESPONSE, 5, bytes([ErrorCode.OK]) + struct.pack("<I", 0))
    transport.to_read += encode_frame(Command.DOWNLOAD_END_RESPONSE, 6, bytes([ErrorCode.OK]))
    transport.to_read += encode_frame(Command.RESET_RESPONSE, 7, bytes([ErrorCode.OK]))
    transport.open()

    # Firmware with custom base address
    fw = FirmwareImage(b"data", base_address=0x08001000)
    service.flash_firmware(fw)

    # Find the DOWNLOAD_START frame and check the Target address (at offset 16 in the frame,
    # but let's be more precise: SOF(1) Ver(1) Cmd(1) Seq(1) Len(2) Payload(N) CRC(2))
    # Payload starts at index 6.
    # DOWNLOAD_START payload: Size(4), CRC(4), Target(4), ...
    # Target address is at payload offset 8, so frame index 6 + 8 = 14.

    # Let's find the frame starting with Command.DOWNLOAD_START
    download_start_frame = None
    offset = 0
    while offset < len(transport.written):
        payload_length = struct.unpack("<H", transport.written[offset + 4:offset + 6])[0]
        frame = transport.written[offset:offset + 8 + payload_length]
        if frame[2] == Command.DOWNLOAD_START:
            download_start_frame = frame
            break
        offset += 8 + payload_length

    assert download_start_frame is not None
    target_address = struct.unpack("<I", download_start_frame[6+8:6+12])[0]
    assert target_address == 0x08001000
