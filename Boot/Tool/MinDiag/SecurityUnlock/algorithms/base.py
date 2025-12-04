"""
Base interface for security key calculation algorithms.

To add a new algorithm:
1. Create a new class inheriting from SecurityAlgorithm
2. Implement calculate_key() method
3. Register in AlgorithmFactory
"""
from abc import ABC, abstractmethod


class SecurityAlgorithm(ABC):
    """Base class for security key calculation algorithms."""
    
    @abstractmethod
    def calculate_key(self, seed_bytes: bytes) -> bytes:
        """
        Calculate security key from seed.
        
        Args:
            seed_bytes: Seed as bytes
            
        Returns:
            bytes: Calculated key
            
        Raises:
            ValueError: If seed format is invalid
        """
        pass
    
    def get_name(self) -> str:
        """
        Get algorithm name.
        
        Returns:
            str: Algorithm name
        """
        return self.__class__.__name__
    
    def get_description(self) -> str:
        """
        Get algorithm description.
        
        Returns:
            str: Algorithm description
        """
        return self.__doc__ or "No description available"
    
    def validate_seed(self, seed_bytes: bytes) -> bool:
        """
        Validate seed format (optional override).
        
        Args:
            seed_bytes: Seed to validate
            
        Returns:
            bool: True if valid
        """
        # Default: accept any non-empty seed
        return len(seed_bytes) > 0
