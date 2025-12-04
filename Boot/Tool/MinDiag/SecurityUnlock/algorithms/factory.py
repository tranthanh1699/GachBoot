"""
Algorithm factory for creating security algorithm instances.

To add a new algorithm:
1. Import your algorithm class
2. Add it to ALGORITHMS dictionary with a unique name
3. Set as default if needed (change DEFAULT_ALGORITHM)
"""
from .base import SecurityAlgorithm
from .xor_rotate import XORRotateAlgorithm
from .simple_xor import SimpleXORAlgorithm
from .xor_u32 import XORU32Algorithm
from .xor_u64 import XORU64Algorithm


class AlgorithmFactory:
    """Factory for creating algorithm instances."""
    
    # Registry of available algorithms
    ALGORITHMS = {
        'xor_rotate': XORRotateAlgorithm,
        'simple_xor': SimpleXORAlgorithm,
        'xor_u32': XORU32Algorithm,
        'xor_u64': XORU64Algorithm,
        # Add your algorithms here:
        # 'aes': AESAlgorithm,
        # 'custom': CustomAlgorithm,
    }
    
    # Default algorithm to use
    DEFAULT_ALGORITHM = 'xor_rotate'
    
    @classmethod
    def create(cls, algorithm_name=None, **kwargs):
        """
        Create algorithm instance.
        
        Args:
            algorithm_name: Algorithm name. If None, uses default.
            **kwargs: Arguments passed to algorithm constructor
            
        Returns:
            SecurityAlgorithm: Algorithm instance
            
        Raises:
            ValueError: If algorithm not found
        """
        name = algorithm_name or cls.DEFAULT_ALGORITHM
        
        if name not in cls.ALGORITHMS:
            available = ', '.join(cls.ALGORITHMS.keys())
            raise ValueError(f"Unknown algorithm '{name}'. Available: {available}")
        
        algorithm_class = cls.ALGORITHMS[name]
        return algorithm_class(**kwargs)
    
    @classmethod
    def get_available_algorithms(cls):
        """
        Get list of available algorithm names.
        
        Returns:
            list: Algorithm names
        """
        return list(cls.ALGORITHMS.keys())
    
    @classmethod
    def get_default_algorithm(cls):
        """
        Get default algorithm name.
        
        Returns:
            str: Default algorithm name
        """
        return cls.DEFAULT_ALGORITHM
