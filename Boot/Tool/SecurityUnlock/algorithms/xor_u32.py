"""
XOR U32 algorithm - XOR seed with 32-bit value.
Matches ECU implementation: key = seed XOR 0x12345678
"""
from .base import SecurityAlgorithm


class XORU32Algorithm(SecurityAlgorithm):
    """
    XOR U32 algorithm for 4-byte seeds.
    key = seed XOR xor_value
    """
    
    def __init__(self, xor_value=0x12345678):
        """
        Initialize algorithm.
        
        Args:
            xor_value: 32-bit XOR value
        """
        self.xor_value = xor_value & 0xFFFFFFFF
    
    def calculate_key(self, seed_bytes):
        """
        Calculate key by XORing seed with xor_value.
        
        Args:
            seed_bytes: Seed as bytes (4 bytes for U32)
            
        Returns:
            bytes: Calculated key (4 bytes)
        """
        if len(seed_bytes) != 4:
            raise ValueError(f"XOR U32 requires 4-byte seed, got {len(seed_bytes)} bytes")
        
        # Convert seed to U32
        seed_u32 = int.from_bytes(seed_bytes, byteorder='big')
        
        # XOR with configured value
        key_u32 = seed_u32 ^ self.xor_value
        
        # Convert back to bytes
        return key_u32.to_bytes(4, byteorder='big')
    
    def get_name(self):
        return "XOR U32"
    
    def get_description(self):
        return f"XOR seed with 0x{self.xor_value:08X}"
