import pytest
from protocol.frame import encode_frame, decode_frame, crc16_ccitt_false
from protocol.commands import Command

def test_crc16():
    # Test vector for CRC16-CCITT-FALSE (often "123456789" -> 0x29B1)
    assert crc16_ccitt_false(b"123456789") == 0x29B1

def test_encode_decode_hello():
    cmd = Command.HELLO
    seq = 0x12
    payload = b"\x01\x00\x00\x00\x00" # Protocol v1, Flags 0
    
    encoded = encode_frame(cmd, seq, payload)
    assert encoded[0] == 0xA5
    assert encoded[2] == Command.HELLO
    assert encoded[3] == 0x12
    
    decoded = decode_frame(encoded)
    assert decoded.command == cmd
    assert decoded.sequence == seq
    assert decoded.payload == payload

def test_invalid_sof():
    with pytest.raises(ValueError, match="Invalid SOF"):
        decode_frame(b"\x00\x01\x01\x00\x00\x00\x00\x00")

def test_checksum_mismatch():
    encoded = list(encode_frame(Command.HELLO, 0, b"test"))
    encoded[-1] ^= 0xFF # Corrupt CRC
    with pytest.raises(ValueError, match="Checksum mismatch"):
        decode_frame(bytes(encoded))

def test_payload_too_large():
    with pytest.raises(ValueError, match="Payload too large"):
        encode_frame(Command.DATA, 0, b"A" * 257)
