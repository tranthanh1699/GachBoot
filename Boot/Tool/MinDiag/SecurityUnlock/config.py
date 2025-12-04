"""
Configuration for Security Access Key Calculator.

Supports multiple security levels with different algorithms.
Each security level can use a different algorithm and configuration.

To change algorithm for a level:
1. Modify the 'algorithm' field in SECURITY_LEVELS
2. Update the 'config' dict with algorithm-specific parameters

To add a new security level:
1. Add entry to SECURITY_LEVELS dict
2. Specify algorithm name and config
"""

# Security level to algorithm mapping
# Format: level (int) -> {'algorithm': str, 'config': dict}
SECURITY_LEVELS = {
    0x01: {
        'algorithm': 'xor_u32',
        'config': {
            'xor_value': 0x12345678,  # From ECU: key = seed XOR 0x12345678
        },
        'description': 'Programming session security'
    },
    0x02: {
        'algorithm': 'xor_u64',
        'config': {
            'xor_value': 0x123456789ABCDEF0,  # From ECU level 2
        },
        'description': 'Extended diagnostic security (Level 2)'
    },
    # Add more security levels as needed
}

# Default security level (if not specified in CLI)
DEFAULT_SECURITY_LEVEL = 0x01

# Fallback algorithm (if level not found in SECURITY_LEVELS)
DEFAULT_ALGORITHM = 'xor_rotate'
DEFAULT_ALGORITHM_CONFIG = {
    'key_pattern': [0xA5, 0x5A, 0xC3, 0x3C, 0x96, 0x69, 0xF0, 0x0F],
}

# Seed validation
EXPECTED_SEED_LENGTHS = [4, 8]  # Typical UDS seed lengths (bytes)
WARN_ON_UNUSUAL_LENGTH = True   # Show warning for non-standard lengths

# Output format
OUTPUT_UPPERCASE = True          # Output key in uppercase
OUTPUT_WITH_SPACES = False       # Add spaces between bytes (e.g., "01 02 03 04")

# Debug mode
DEBUG = False                    # Enable debug output to stderr
