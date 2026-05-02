from .transport_base import Transport

class FakeTransport(Transport):
    def __init__(self):
        self._is_open = False
        self.to_read = b""
        self.written = b""

    def open(self):
        self._is_open = True

    def close(self):
        self._is_open = False

    def is_open(self) -> bool:
        return self._is_open

    def write(self, data: bytes):
        if self._is_open:
            self.written += data

    def read(self, size: int, timeout_ms: int) -> bytes:
        if not self._is_open:
            return b""
        data = self.to_read[:size]
        self.to_read = self.to_read[size:]
        return data

    def read_until_sof(self, sof: int, timeout_ms: int) -> bytes:
        if not self._is_open:
            return b""
        idx = self.to_read.find(bytes([sof]))
        if idx != -1:
            data = self.to_read[idx:idx+1]
            self.to_read = self.to_read[idx+1:]
            return data
        return b""
