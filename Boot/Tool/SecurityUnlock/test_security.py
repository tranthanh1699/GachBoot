"""
Test cases for SecurityUnlock calculator.
"""
from SecurityUnlock import SecurityCalculator
from algorithms import AlgorithmFactory
import config


def test_basic_calculation():
    """Test basic key calculation."""
    print("Test 1: Basic 4-byte seed")
    calculator = SecurityCalculator()
    seed = bytes([0x01, 0x02, 0x03, 0x04])
    key = calculator.calculate_key(seed)
    print(f"  Seed: {seed.hex().upper()}")
    print(f"  Key:  {key.hex().upper()}")
    assert len(key) == len(seed), "Key length should match seed length"
    print("  ✓ PASSED\n")


def test_8byte_seed():
    """Test 8-byte seed calculation."""
    print("Test 2: 8-byte seed")
    calculator = SecurityCalculator()
    seed = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
    key = calculator.calculate_key(seed)
    print(f"  Seed: {seed.hex().upper()}")
    print(f"  Key:  {key.hex().upper()}")
    assert len(key) == len(seed), "Key length should match seed length"
    print("  ✓ PASSED\n")


def test_zero_seed():
    """Test all-zero seed."""
    print("Test 3: All-zero seed")
    calculator = SecurityCalculator()
    seed = bytes([0x00, 0x00, 0x00, 0x00])
    key = calculator.calculate_key(seed)
    print(f"  Seed: {seed.hex().upper()}")
    print(f"  Key:  {key.hex().upper()}")
    assert key != seed, "Key should be different from all-zero seed"
    print("  ✓ PASSED\n")


def test_max_seed():
    """Test all-0xFF seed."""
    print("Test 4: All-0xFF seed")
    calculator = SecurityCalculator()
    seed = bytes([0xFF, 0xFF, 0xFF, 0xFF])
    key = calculator.calculate_key(seed)
    print(f"  Seed: {seed.hex().upper()}")
    print(f"  Key:  {key.hex().upper()}")
    assert key != seed, "Key should be different from all-0xFF seed"
    print("  ✓ PASSED\n")


def test_deterministic():
    """Test that same seed always produces same key."""
    print("Test 5: Deterministic calculation")
    calculator = SecurityCalculator()
    seed = bytes([0xAA, 0xBB, 0xCC, 0xDD])
    key1 = calculator.calculate_key(seed)
    key2 = calculator.calculate_key(seed)
    print(f"  Seed: {seed.hex().upper()}")
    print(f"  Key1: {key1.hex().upper()}")
    print(f"  Key2: {key2.hex().upper()}")
    assert key1 == key2, "Same seed should always produce same key"
    print("  ✓ PASSED\n")


def test_seed_validation():
    """Test seed validation."""
    print("Test 6: Seed validation")
    
    # Valid seeds
    assert SecurityCalculator.validate_seed("01020304"), "4-byte hex should be valid"
    assert SecurityCalculator.validate_seed("0102030405060708"), "8-byte hex should be valid"
    assert SecurityCalculator.validate_seed("01 02 03 04"), "Hex with spaces should be valid"
    
    # Invalid seeds
    assert not SecurityCalculator.validate_seed("123"), "Odd length should be invalid"
    assert not SecurityCalculator.validate_seed("GGHHIIJJ"), "Non-hex should be invalid"
    assert not SecurityCalculator.validate_seed(""), "Empty should be invalid"
    
    print("  ✓ PASSED\n")


def test_known_vectors():
    """Test with known seed/key pairs (if you have them)."""
    print("Test 7: Known test vectors")
    
    # Replace with your actual seed/key pairs from ECU
    test_vectors = [
        # (seed_hex, expected_key_hex)
        # Example: ("01020304", "A1B2C3D4"),
    ]
    
    if not test_vectors:
        print("  ⚠ No test vectors configured")
        print("  Add your ECU's seed/key pairs to verify algorithm\n")
        return
    
    for seed_hex, expected_key_hex in test_vectors:
        calculator = SecurityCalculator()
        seed = bytes.fromhex(seed_hex)
        key = calculator.calculate_key(seed)
        key_hex = key.hex().upper()
        
        print(f"  Seed: {seed_hex}")
        print(f"  Expected: {expected_key_hex}")
        print(f"  Got:      {key_hex}")
        
        assert key_hex == expected_key_hex.upper(), f"Key mismatch for seed {seed_hex}"
        print("  ✓ PASSED")
    
    print()


def test_security_levels():
    """Test different security levels."""
    print("Test 8: Security levels")
    
    seed = bytes([0x01, 0x02, 0x03, 0x04])
    
    # Test level 0x01
    calc1 = SecurityCalculator(security_level=0x01)
    key1 = calc1.calculate_key(seed)
    print(f"  Level 0x01: {seed.hex().upper()} -> {key1.hex().upper()}")
    
    # Test level 0x03
    calc3 = SecurityCalculator(security_level=0x03)
    key3 = calc3.calculate_key(seed)
    print(f"  Level 0x03: {seed.hex().upper()} -> {key3.hex().upper()}")
    
    # Keys should be different for different levels
    assert key1 != key3, "Different levels should produce different keys"
    
    print("  ✓ PASSED\n")


def test_default_level():
    """Test default security level."""
    print("Test 9: Default security level")
    
    seed = bytes([0x01, 0x02, 0x03, 0x04])
    
    # Without specifying level (uses default)
    calc_default = SecurityCalculator()
    key_default = calc_default.calculate_key(seed)
    
    # With explicit default level
    calc_explicit = SecurityCalculator(security_level=config.DEFAULT_SECURITY_LEVEL)
    key_explicit = calc_explicit.calculate_key(seed)
    
    print(f"  Default key: {key_default.hex().upper()}")
    print(f"  Explicit key: {key_explicit.hex().upper()}")
    
    assert key_default == key_explicit, "Default and explicit should match"
    print("  ✓ PASSED\n")


def main():
    """Run all tests."""
    print("=" * 50)
    print("Security Access Key Calculator - Test Suite")
    print("=" * 50)
    print()
    
    try:
        test_basic_calculation()
        test_8byte_seed()
        test_zero_seed()
        test_max_seed()
        test_deterministic()
        test_seed_validation()
        test_known_vectors()
        test_security_levels()
        test_default_level()
        
        print("=" * 50)
        print("All tests PASSED! ✓")
        print("=" * 50)
        
    except AssertionError as e:
        print()
        print("=" * 50)
        print(f"Test FAILED: {e}")
        print("=" * 50)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
