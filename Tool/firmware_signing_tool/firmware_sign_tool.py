#!/usr/bin/env python3

import argparse
import binascii
import os
import struct
import sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

# Default Section IDs
DEFAULT_APP_SECTION_ID = 0xA501
DEFAULT_SIGNATURE_SECTION_ID = 0x5A02

SIGNATURE_SIZE_BYTES = 256
HEADER_SIZE_BYTES = 10

def calculate_crc32(data: bytes) -> int:
    """Standard Ethernet/ZIP CRC32 calculation."""
    return binascii.crc32(data) & 0xFFFFFFFF

def parse_id(id_str: str) -> int:
    """Parse ID as hex or decimal."""
    try:
        if id_str.lower().startswith("0x"):
            return int(id_str, 16)
        return int(id_str)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid ID: {id_str}")

def sign_firmware(app_data: bytes, private_key_path: str) -> bytes:
    """Sign application data using RSA-2048 SHA-256 PKCS#1 v1.5."""
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )
    
    signature = private_key.sign(
        app_data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    if len(signature) != SIGNATURE_SIZE_BYTES:
        raise ValueError(f"Generated signature size is {len(signature)}, expected {SIGNATURE_SIZE_BYTES}")
        
    return signature

def create_package(app_data: bytes, signature: bytes, app_id: int, sig_id: int) -> bytes:
    """Generate binary package: [Header App] + [App Binary] + [Header Signature] + [Signature]."""
    
    # App Header: uint16 id, uint32 size, uint32 crc32
    app_crc = calculate_crc32(app_data)
    app_header = struct.pack("<HII", app_id, len(app_data), app_crc)
    
    # Signature Header: uint16 id, uint32 size, uint32 crc32
    sig_crc = calculate_crc32(signature)
    sig_header = struct.pack("<HII", sig_id, len(signature), sig_crc)
    
    return app_header + app_data + sig_header + signature

def inspect_package(package_path: str, app_id_expected: int, sig_id_expected: int):
    """Inspect and validate a signed package."""
    if not os.path.exists(package_path):
        print(f"Error: Package file '{package_path}' not found.")
        sys.exit(1)
        
    with open(package_path, "rb") as f:
        data = f.read()
        
    if len(data) < (HEADER_SIZE_BYTES * 2) + SIGNATURE_SIZE_BYTES:
        print("Error: Package too small to be valid.")
        sys.exit(1)
        
    # Parse App Header
    app_id, app_size, app_crc = struct.unpack("<HII", data[:HEADER_SIZE_BYTES])
    app_binary = data[HEADER_SIZE_BYTES : HEADER_SIZE_BYTES + app_size]
    
    # Parse Signature Header
    sig_header_offset = HEADER_SIZE_BYTES + app_size
    sig_id, sig_size, sig_crc = struct.unpack("<HII", data[sig_header_offset : sig_header_offset + HEADER_SIZE_BYTES])
    signature = data[sig_header_offset + HEADER_SIZE_BYTES :]
    
    print(f"App Header:")
    print(f"  ID    : 0x{app_id:04X}")
    print(f"  Size  : {app_size} bytes")
    print(f"  CRC32 : 0x{app_crc:08X}")
    
    print(f"\nSignature Header:")
    print(f"  ID    : 0x{sig_id:04X}")
    print(f"  Size  : {sig_size} bytes")
    print(f"  CRC32 : 0x{sig_crc:08X}")
    
    print(f"\nTotal package size: {len(data)} bytes")
    
    # Validation
    valid = True
    if app_id != app_id_expected:
        print(f"[FAIL] App ID mismatch (Expected 0x{app_id_expected:04X})")
        valid = False
    
    if sig_id != sig_id_expected:
        print(f"[FAIL] Signature ID mismatch (Expected 0x{sig_id_expected:04X})")
        valid = False
        
    if calculate_crc32(app_binary) != app_crc:
        print("[FAIL] App binary CRC32 mismatch")
        valid = False
        
    if calculate_crc32(signature) != sig_crc:
        print("[FAIL] Signature CRC32 mismatch")
        valid = False
        
    if len(signature) != SIGNATURE_SIZE_BYTES:
        print(f"[FAIL] Signature size invalid: {len(signature)} bytes")
        valid = False
    
    if valid:
        print("\nValidation result: [SUCCESS]")
    else:
        print("\nValidation result: [FAILED]")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="GachBoot Firmware Signing Tool")
    parser.add_argument("--input", help="Application binary to sign")
    parser.add_argument("--private-key", help="RSA-2048 private key in PEM format")
    parser.add_argument("--output", help="Output signed package binary")
    parser.add_argument("--app-id", type=parse_id, default=DEFAULT_APP_SECTION_ID, 
                        help=f"Application section ID (default: 0x{DEFAULT_APP_SECTION_ID:04X})")
    parser.add_argument("--signature-id", type=parse_id, default=DEFAULT_SIGNATURE_SECTION_ID, 
                        help=f"Signature section ID (default: 0x{DEFAULT_SIGNATURE_SECTION_ID:04X})")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--inspect", help="Inspect and validate an existing signed package")
    
    args = parser.parse_args()
    
    if args.inspect:
        inspect_package(args.inspect, args.app_id, args.signature_id)
        return

    # For signing mode, these are required
    if not args.input or not args.private_key or not args.output:
        parser.print_help()
        sys.exit(1)
        
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)
        
    if not os.path.exists(args.private_key):
        print(f"Error: Private key '{args.private_key}' not found.")
        sys.exit(1)

    try:
        with open(args.input, "rb") as f:
            app_data = f.read()
            
        if not app_data:
            print("Error: Input application binary is empty.")
            sys.exit(1)
            
        if args.verbose:
            print(f"Read {len(app_data)} bytes from {args.input}")
            print(f"Signing with {args.private_key}...")
            
        signature = sign_firmware(app_data, args.private_key)
        
        if args.verbose:
            print(f"Generated {len(signature)} byte signature.")
            print(f"Creating package with App ID 0x{args.app_id:04X} and Signature ID 0x{args.signature_id:04X}...")
            
        package = create_package(app_data, signature, args.app_id, args.signature_id)
        
        with open(args.output, "wb") as f:
            f.write(package)
            
        if args.verbose:
            print(f"Saved signed package to {args.output} ({len(package)} bytes)")
        else:
            print(f"Successfully created: {args.output}")
            
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
