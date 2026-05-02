import serial
import time
from .transport_base import Transport

class SerialTransport(Transport):
    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.ser: serial.Serial = None

    def open(self):
        if not self.ser:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0)

    def close(self):
        if self.ser:
            self.ser.close()
            self.ser = None

    def is_open(self) -> bool:
        return self.ser is not None and self.ser.is_open

    def write(self, data: bytes):
        if self.is_open():
            self.ser.write(data)

    def read(self, size: int, timeout_ms: int) -> bytes:
        if not self.is_open():
            return b""
        
        start_time = time.time()
        buf = b""
        while len(buf) < size:
            if (time.time() - start_time) * 1000 > timeout_ms:
                break
            chunk = self.ser.read(size - len(buf))
            if chunk:
                buf += chunk
            else:
                time.sleep(0.001)
        return buf

    def read_until_sof(self, sof: int, timeout_ms: int) -> bytes:
        if not self.is_open():
            return b""
        
        start_time = time.time()
        while True:
            if (time.time() - start_time) * 1000 > timeout_ms:
                return b""
            byte = self.ser.read(1)
            if byte:
                if byte[0] == sof:
                    return byte
            else:
                time.sleep(0.001)
