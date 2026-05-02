from abc import ABC, abstractmethod

class Transport(ABC):
    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def is_open(self) -> bool:
        pass

    @abstractmethod
    def write(self, data: bytes):
        pass

    @abstractmethod
    def read(self, size: int, timeout_ms: int) -> bytes:
        pass

    @abstractmethod
    def read_until_sof(self, sof: int, timeout_ms: int) -> bytes:
        pass
