"""
Security Access Key Calculator for UDS Service 0x27

This tool calculates the security key from a given seed using configurable algorithms.
Supports multiple security levels with different algorithms.

Usage:
    SecurityUnlock.exe [security_level] <seed_hex>
    
Examples:
    SecurityUnlock.exe 01020304                  # Uses default level (0x01)
    SecurityUnlock.exe 0x01 01020304             # Explicit level 0x01
    SecurityUnlock.exe 3 01020304                # Level 0x03 (decimal or hex)
    
Output: Key in hex format (e.g., A1B2C3D4)

To configure security levels:
    Edit config.py SECURITY_LEVELS dict
"""
import sys
from algorithms import AlgorithmFactory
import config


class SecurityCalculator:
    """
    Security access key calculator with pluggable algorithms.
    Supports multiple security levels.
    """
    
    def __init__(self, security_level=None, algorithm_name=None):
        """
        Initialize calculator.
        
        Args:
            security_level: Security level (int). If None, uses DEFAULT_SECURITY_LEVEL
            algorithm_name: Force specific algorithm (overrides level config)
        """
        self.security_level = security_level if security_level is not None else config.DEFAULT_SECURITY_LEVEL
        
        # Get algorithm config for this security level
        if self.security_level in config.SECURITY_LEVELS:
            level_config = config.SECURITY_LEVELS[self.security_level]
            algo_name = algorithm_name or level_config['algorithm']
            algo_config = level_config['config']
            self.description = level_config.get('description', '')
        else:
            # Fallback to default
            algo_name = algorithm_name or config.DEFAULT_ALGORITHM
            algo_config = config.DEFAULT_ALGORITHM_CONFIG
            self.description = f'Unknown level (using default)'
            if config.DEBUG:
                print(f"Warning: Security level 0x{self.security_level:02X} not in config, using default", 
                      file=sys.stderr)
        
        try:
            self.algorithm = AlgorithmFactory.create(algo_name, **algo_config)
            if config.DEBUG:
                print(f"SecurityCalculator initialized:", file=sys.stderr)
                print(f"  Level: 0x{self.security_level:02X} - {self.description}", file=sys.stderr)
                print(f"  Algorithm: {self.algorithm.get_name()}", file=sys.stderr)
        except ValueError as e:
            print(f"Error creating algorithm: {e}", file=sys.stderr)
            sys.exit(1)
    
    def calculate_key(self, seed_bytes):
        """
        Calculate security key from seed using configured algorithm.
        
        Args:
            seed_bytes: Seed as bytes
            
        Returns:
            bytes: Calculated key
        """
        return self.algorithm.calculate_key(seed_bytes)
    
    @staticmethod
    def validate_seed(seed_hex):
        """
        Validate seed format.
        
        Args:
            seed_hex: Seed as hex string
            
        Returns:
            bool: True if valid
        """
        # Remove spaces and dashes
        seed_hex = seed_hex.replace(" ", "").replace("-", "")
        
        # Check if hex
        try:
            int(seed_hex, 16)
        except ValueError:
            return False
        
        # Check even length (whole bytes)
        if len(seed_hex) % 2 != 0:
            return False
        
        # Check length if configured
        seed_len = len(seed_hex) // 2
        if config.WARN_ON_UNUSUAL_LENGTH and seed_len not in config.EXPECTED_SEED_LENGTHS:
            expected = ', '.join(str(l) for l in config.EXPECTED_SEED_LENGTHS)
            print(f"Warning: Unusual seed length ({seed_len} bytes). Expected: {expected} bytes.", 
                  file=sys.stderr)
        
        return True


def parse_security_level(level_str):
    """
    Parse security level from string.
    
    Args:
        level_str: Security level as string (e.g., "1", "0x01", "3")
        
    Returns:
        int: Security level value
    """
    try:
        # Handle hex format (0x01) or decimal (1)
        if level_str.lower().startswith('0x'):
            return int(level_str, 16)
        else:
            return int(level_str)
    except ValueError:
        raise ValueError(f"Invalid security level format: {level_str}")


def main():
    """Main entry point."""
    
    # Parse arguments
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Error: Invalid arguments", file=sys.stderr)
        print("Usage: SecurityUnlock.exe [security_level] <seed_hex>", file=sys.stderr)
        print("", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  SecurityUnlock.exe 01020304           # Uses default level", file=sys.stderr)
        print("  SecurityUnlock.exe 0x01 01020304      # Level 0x01", file=sys.stderr)
        print("  SecurityUnlock.exe 3 01020304         # Level 0x03", file=sys.stderr)
        print("", file=sys.stderr)
        print("Configured levels:", file=sys.stderr)
        for level, cfg in sorted(config.SECURITY_LEVELS.items()):
            desc = cfg.get('description', '')
            algo = cfg.get('algorithm', '')
            print(f"  0x{level:02X} - {desc} ({algo})", file=sys.stderr)
        sys.exit(1)
    
    # Determine if first arg is security level or seed
    if len(sys.argv) == 3:
        # Format: SecurityUnlock.exe <level> <seed>
        try:
            security_level = parse_security_level(sys.argv[1])
            seed_hex = sys.argv[2]
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Format: SecurityUnlock.exe <seed>
        security_level = None  # Will use default
        seed_hex = sys.argv[1]
    
    # Validate seed
    if not SecurityCalculator.validate_seed(seed_hex):
        print(f"Error: Invalid seed format: {seed_hex}", file=sys.stderr)
        print("Seed must be hex string with even length", file=sys.stderr)
        sys.exit(1)
    
    # Clean seed
    seed_hex = seed_hex.replace(" ", "").replace("-", "")
    
    try:
        # Convert to bytes
        seed_bytes = bytes.fromhex(seed_hex)
        
        # Create calculator with security level
        calculator = SecurityCalculator(security_level=security_level)
        
        # Calculate key
        key_bytes = calculator.calculate_key(seed_bytes)
        
        # Format output
        key_hex = key_bytes.hex()
        if config.OUTPUT_UPPERCASE:
            key_hex = key_hex.upper()
        
        if config.OUTPUT_WITH_SPACES:
            key_hex = ' '.join(key_hex[i:i+2] for i in range(0, len(key_hex), 2))
        
        # Output key
        print(key_hex)
        
        if config.DEBUG:
            print(f"Seed: {seed_hex}", file=sys.stderr)
            print(f"Key:  {key_hex}", file=sys.stderr)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        if config.DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
