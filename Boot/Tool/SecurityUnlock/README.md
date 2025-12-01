# Security Access Key Calculator

## Overview
This tool calculates the security access key for UDS Service 0x27 from a given seed.
Supports **multiple security levels** with different algorithms per level.

## Features
- ✅ Multiple security levels (0x01, 0x03, 0x05, etc.)
- ✅ Different algorithms per level
- ✅ Pluggable algorithm architecture
- ✅ Easy to add new levels/algorithms
- ✅ Command-line interface
- ✅ Configurable via `config.py`

## Usage

### Command Line
```bash
# Use default security level
python SecurityUnlock.py <seed_hex>

# Specify security level (hex or decimal)
python SecurityUnlock.py <security_level> <seed_hex>
```

### Examples
```bash
# Default level (0x01)
python SecurityUnlock.py 01020304
# Output: 49B08170

# Explicit level 0x01
python SecurityUnlock.py 0x01 01020304
# Output: 49B08170

# Level 0x03 (decimal format)
python SecurityUnlock.py 3 01020304
# Output: 20406080

# Level 0x05 (different algorithm)
python SecurityUnlock.py 0x05 01020304
# Output: ABA8A9AE

# With spaces (will be stripped)
python SecurityUnlock.py 0x01 "01 02 03 04"
# Output: 49B08170
```

### Help
```bash
python SecurityUnlock.py
# Shows configured security levels and usage
```

### As Executable
```bash
SecurityUnlock.exe 0x01 01020304
```

## Configuration

### Security Levels
Edit `config.py` to configure security levels:

```python
SECURITY_LEVELS = {
    0x01: {
        'algorithm': 'xor_rotate',
        'config': {
            'key_pattern': [0xA5, 0x5A, 0xC3, 0x3C, 0x96, 0x69, 0xF0, 0x0F],
        },
        'description': 'Programming session security'
    },
    0x03: {
        'algorithm': 'xor_rotate',
        'config': {
            'key_pattern': [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88],
        },
        'description': 'Extended diagnostic security'
    },
    0x05: {
        'algorithm': 'simple_xor',
        'config': {
            'xor_key': 0xAA,
        },
        'description': 'Development security'
    },
}
```

### Available Algorithms

#### 1. `xor_rotate`
- XORs seed with key pattern
- Rotates result left by 1 bit
- Pattern repeats for long seeds

**Config**:
```python
'config': {
    'key_pattern': [0xA5, 0x5A, 0xC3, 0x3C, 0x96, 0x69, 0xF0, 0x0F],
}
```

#### 2. `simple_xor`
- XORs each byte with fixed value
- Simple and fast

**Config**:
```python
'config': {
    'xor_key': 0xAA,
}
```

## Output
- **Success**: Key as uppercase hex string (no spaces)
- **Error**: Error message to stderr, exit code 1

## Building Executable

### Using PyInstaller
```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --name SecurityUnlock SecurityUnlock.py

# Output: dist/SecurityUnlock.exe
```

### Build Script (Windows)
```bash
build.bat
```

## Integration with MinTool

1. Build the executable:
   ```bash
   cd Tool/SecurityUnlock
   build.bat
   ```

2. Configure in MinTool:
   - Open MinTool
   - Config → Settings
   - Security Access EXE: Browse to `SecurityUnlock.exe`
   - Save

3. Use in MinTool:
   - Tools → Security Access (0x27)
   - Request Seed (sends 27 01)
   - Enter seed from response
   - Calculate & Send Key

## Customization

### Add New Security Level
1. Edit `config.py`:
```python
SECURITY_LEVELS = {
    # ... existing levels ...
    0x07: {
        'algorithm': 'xor_rotate',  # or 'simple_xor', or your custom algorithm
        'config': {
            'key_pattern': [0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0],
        },
        'description': 'Factory security'
    },
}
```

2. Use new level:
```bash
python SecurityUnlock.py 0x07 01020304
```

### Add New Algorithm

1. Create new algorithm file `algorithms/my_algorithm.py`:
```python
from .base import SecurityAlgorithm

class MyAlgorithm(SecurityAlgorithm):
    def __init__(self, **kwargs):
        self.config = kwargs
    
    def calculate_key(self, seed_bytes):
        # Your algorithm implementation
        key = bytearray()
        for byte in seed_bytes:
            key.append(byte ^ 0xFF)  # Example: invert bits
        return bytes(key)
    
    def get_name(self):
        return "My Custom Algorithm"
```

2. Register in `algorithms/factory.py`:
```python
from .my_algorithm import MyAlgorithm

class AlgorithmFactory:
    ALGORITHMS = {
        'xor_rotate': XORRotateAlgorithm,
        'simple_xor': SimpleXORAlgorithm,
        'my_algo': MyAlgorithm,  # Add here
    }
```

3. Export in `algorithms/__init__.py`:
```python
from .my_algorithm import MyAlgorithm

__all__ = [..., 'MyAlgorithm']
```

4. Configure in `config.py`:
```python
SECURITY_LEVELS = {
    0x09: {
        'algorithm': 'my_algo',
        'config': {
            # Your algorithm-specific config
        },
        'description': 'Custom algorithm level'
    },
}
```

### Change Default Level
Edit `config.py`:
```python
DEFAULT_SECURITY_LEVEL = 0x03  # Change to your preferred default
```

```python
KEY_PATTERN = [0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0]
```

### Add Security Levels
The current implementation works for any seed length. For level-specific algorithms:

```python
@staticmethod
def calculate_key(seed_bytes, level=1):
    if level == 1:
        # Level 1 algorithm (4-byte)
        return calculate_level_1(seed_bytes)
    elif level == 2:
        # Level 2 algorithm (8-byte)
        return calculate_level_2(seed_bytes)
```

## Testing

### Test Script
```bash
python test_security.py
```

### Manual Testing
```bash
# Test with known seed/key pairs
python SecurityUnlock.py 01020304
# Verify output matches expected key

# Test error handling
python SecurityUnlock.py invalid
python SecurityUnlock.py
python SecurityUnlock.py 123  # Odd length
```

## Security Notes

⚠️ **Important**: This is a demonstration implementation!

For production use:
1. **Use proper cryptographic algorithms** (AES, HMAC, etc.)
2. **Implement HSM integration** if required
3. **Add challenge-response verification**
4. **Follow AUTOSAR SecOC standards**
5. **Protect key patterns** (don't hardcode in source)

## File Structure
```
SecurityUnlock/
├── SecurityUnlock.py       # Main calculator
├── README.md              # This file
├── build.bat              # Build script
├── test_security.py       # Test cases
└── requirements.txt       # Dependencies
```

## Exit Codes
- `0`: Success, key written to stdout
- `1`: Error (invalid seed, exception, etc.)

## Dependencies
None - pure Python 3 standard library

## Compatibility
- Python 3.6+
- Windows/Linux/macOS
- 32-bit and 64-bit

---
Last Updated: December 1, 2025
Part of GachBoot MinTool Project
