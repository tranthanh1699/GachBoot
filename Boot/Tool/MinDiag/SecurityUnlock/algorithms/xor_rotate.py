"""
XOR + Rotate algorithm for security key calculation.

Algorithm:
1. XOR each seed byte with pattern byte
2. Rotate result left by 1 bit
3. Cycle pattern if seed is longer

This is the default algorithm.
"""
from .base import SecurityAlgorithm


class XORRotateAlgorithm(SecurityAlgorithm):
    """XOR with key pattern + bit rotation algorithm."""
    
    # Default key pattern - can be overridden in constructor
    DEFAULT_KEY_PATTERN = [0xA5, 0x5A, 0xC3, 0x3C, 0x96, 0x69, 0xF0, 0x0F]
    
    def __init__(self, key_pattern=None):
        """
        Initialize algorithm with optional custom key pattern.
        
        Args:
            key_pattern: Custom key pattern (list of bytes). If None, uses default.
        """
        self.key_pattern = key_pattern or self.DEFAULT_KEY_PATTERN
    
    def calculate_key(self, seed_bytes: bytes) -> bytes:
        """
        Calculate key using XOR + rotate algorithm.
        
        Args:
            seed_bytes: Seed as bytes
            
        Returns:
            bytes: Calculated key
        """
        key = bytearray()
        
        for i, seed_byte in enumerate(seed_bytes):
            # XOR with key pattern (cycle through pattern if seed is longer)
            pattern_byte = self.key_pattern[i % len(self.key_pattern)]
            
            # Calculate key byte: XOR + rotate left by 1
            key_byte = seed_byte ^ pattern_byte
            key_byte = ((key_byte << 1) | (key_byte >> 7)) & 0xFF
            
            key.append(key_byte)
        
        return bytes(key)
    
    def validate_seed(self, seed_bytes: bytes) -> bool:
        """
        Validate seed (typically 4 or 8 bytes).
        
        Args:
            seed_bytes: Seed to validate
            
        Returns:
            bool: True if valid
        """
        return len(seed_bytes) in [4, 8]
    
    def get_description(self) -> str:
        """Get algorithm description."""
        return f"XOR + Rotate (Pattern: {len(self.key_pattern)} bytes)"
