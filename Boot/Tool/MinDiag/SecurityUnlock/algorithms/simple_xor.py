"""
Simple XOR algorithm for security key calculation.
"""
from .base import SecurityAlgorithm


class SimpleXORAlgorithm(SecurityAlgorithm):
    """
    Simple XOR algorithm.
    XORs each byte of seed with a fixed key.
    """
    
    def __init__(self, xor_key=0xAA):
        """
        Initialize algorithm.
        
        Args:
            xor_key: Single byte XOR key (0x00-0xFF)
        """
        self.xor_key = xor_key & 0xFF
    
    def calculate_key(self, seed_bytes):
        """
        Calculate key by XORing each seed byte with xor_key.
        
        Args:
            seed_bytes: Seed as bytes
            
        Returns:
            bytes: Calculated key (same length as seed)
        """
        return bytes([b ^ self.xor_key for b in seed_bytes])
    
    def get_name(self):
        return "Simple XOR"
    
    def get_description(self):
        return f"XOR each byte with 0x{self.xor_key:02X}"
