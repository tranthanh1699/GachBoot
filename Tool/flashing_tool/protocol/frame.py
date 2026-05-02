import struct
from typing import NamedTuple, Optional
from .commands import Command

SOF = 0xA5
PROTOCOL_VERSION = 0x01
CRC16_POLY = 0x1021
CRC16_INIT = 0xFFFF

class Frame(NamedTuple):
    version: int
    command: Command
    sequence: int
    payload: bytes

def crc16_ccitt_false(data: bytes) -> int:
    crc = CRC16_INIT
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ CRC16_POLY
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

def encode_frame(command: Command, sequence: int, payload: bytes = b"") -> bytes:
    if len(payload) > 1024:
        raise ValueError("Payload too large (max 1024 bytes)")
    
    # Body consists of Version, Command ID, Sequence, and Length
    length_le = struct.pack("<H", len(payload))
    body = bytes([PROTOCOL_VERSION, int(command), sequence]) + length_le + payload
    
    # Checksum is over the body
    crc = crc16_ccitt_false(body)
    crc_le = struct.pack("<H", crc)
    
    return bytes([SOF]) + body + crc_le

def decode_frame(raw: bytes) -> Frame:
    if len(raw) < 8:
        raise ValueError("Frame too short")
    
    if raw[0] != SOF:
        raise ValueError(f"Invalid SOF: expected 0x{SOF:02X}, got 0x{raw[0]:02X}")
    
    version = raw[1]
    command_id = raw[2]
    sequence = raw[3]
    payload_length = struct.unpack("<H", raw[4:6])[0]
    
    expected_total_len = 8 + payload_length
    if len(raw) != expected_total_len:
        raise ValueError(f"Invalid frame length: expected {expected_total_len}, got {len(raw)}")
    
    payload = raw[6:6+payload_length]
    received_crc = struct.unpack("<H", raw[6+payload_length:8+payload_length])[0]
    
    # Checksum is calculated over Version, Command ID, Sequence, Length, and Payload
    calculated_crc = crc16_ccitt_false(raw[1:6+payload_length])
    
    if received_crc != calculated_crc:
        raise ValueError(f"Checksum mismatch: received 0x{received_crc:04X}, calculated 0x{calculated_crc:04X}")
    
    try:
        command = Command(command_id)
    except ValueError:
        # We still return the frame but the command might be unknown to our enum
        # This is handled by the protocol layer
        raise ValueError(f"Unknown command ID: 0x{command_id:02X}")

    return Frame(version, command, sequence, payload)
