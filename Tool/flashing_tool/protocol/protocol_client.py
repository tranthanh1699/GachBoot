import struct
from typing import Optional
from transport.transport_base import Transport
from .frame import encode_frame, decode_frame, Frame, SOF
from .commands import Command
from .errors import ErrorCode

class ProtocolError(Exception):
    def __init__(self, command: Command, error_code: ErrorCode):
        self.command = command
        self.error_code = error_code
        super().__init__(f"Protocol error for {command.name}: {error_code.name}")

class ProtocolClient:
    def __init__(self, transport: Transport):
        self.transport = transport
        self.sequence = 0
        self.timeout_ms = 1000

    def _next_sequence(self) -> int:
        self.sequence = (self.sequence + 1) & 0xFF
        return self.sequence

    def request_response(self, command: Command, payload: bytes = b"") -> Frame:
        seq = self._next_sequence()
        tx_frame = encode_frame(command, seq, payload)
        
        self.transport.write(tx_frame)
        
        # Read until SOF
        sof_byte = self.transport.read_until_sof(SOF, self.timeout_ms)
        if not sof_byte:
            raise TimeoutError(f"Timeout waiting for SOF of {command.name} response")
        
        # Read header (Version, Command, Sequence, Length) = 5 bytes
        header = self.transport.read(5, self.timeout_ms)
        if len(header) < 5:
            raise TimeoutError(f"Timeout waiting for header of {command.name} response")
        
        payload_length = struct.unpack("<H", header[3:5])[0]
        
        # Read payload + CRC = payload_length + 2 bytes
        rest = self.transport.read(payload_length + 2, self.timeout_ms)
        if len(rest) < payload_length + 2:
            raise TimeoutError(f"Timeout waiting for payload/CRC of {command.name} response")
        
        rx_raw = sof_byte + header + rest
        rx_frame = decode_frame(rx_raw)
        
        if rx_frame.command == Command.ERROR_RESPONSE:
            req_cmd_id = rx_frame.payload[0]
            err_code_id = rx_frame.payload[1]
            raise ProtocolError(Command(req_cmd_id), ErrorCode(err_code_id))
        
        if rx_frame.sequence != seq:
            raise ValueError(f"Sequence mismatch: expected {seq}, got {rx_frame.sequence}")
            
        return rx_frame
