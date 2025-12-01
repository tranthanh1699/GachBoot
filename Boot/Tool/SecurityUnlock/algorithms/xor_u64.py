"""
XOR U64 algorithm - XOR seed with 64-bit value.
Matches ECU Level 2: key = seed XOR 0x123456789ABCDEF0
"""
from .base import SecurityAlgorithm


class XORU64Algorithm(SecurityAlgorithm):
    """
    XOR U64 algorithm for 8-byte seeds.
    key = seed XOR xor_value
    """
    
    def __init__(self, xor_value=0x123456789ABCDEF0):
        """
        Initialize algorithm.
        
        Args:
            xor_value: 64-bit XOR value
        """
        self.xor_value = xor_value & 0xFFFFFFFFFFFFFFFF
    
    def calculate_key(self, seed_bytes):
        """
        Calculate key by XORing seed with xor_value.
        
        Args:
            seed_bytes: Seed as bytes (8 bytes for U64)
            
        Returns:
            bytes: Calculated key (8 bytes)
        """
        if len(seed_bytes) != 8:
            raise ValueError(f"XOR U64 requires 8-byte seed, got {len(seed_bytes)} bytes")
        
        # Convert seed to U64
        seed_u64 = int.from_bytes(seed_bytes, byteorder='big')
        
        # XOR with configured value
        key_u64 = seed_u64 ^ self.xor_value
        
        # Convert back to bytes
        return key_u64.to_bytes(8, byteorder='big')
    
    def get_name(self):
        return "XOR U64"
    
    def get_description(self):
        return f"XOR seed with 0x{self.xor_value:016X}"
