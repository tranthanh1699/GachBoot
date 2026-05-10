import sys
import os
import argparse
import struct

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from firmware.firmware_image import FirmwareImage

APP_SECTION_ID = 0xA501
SIGNATURE_SECTION_ID = 0x5A02
SECTION_HEADER_FORMAT = "<HII"

def parse_u16(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFFFF:
        raise argparse.ArgumentTypeError("value must fit in uint16_t")
    return parsed

def inspect_package(path: str) -> None:
    fw = FirmwareImage.from_file(path)
    if fw.signature is None:
        print("Raw application image")
    else:
        print("Signed firmware package")
        print(f"Application size: {fw.size} bytes")
        print(f"Application CRC32: 0x{fw.crc32:08X}")
        print(f"Signature size: {len(fw.signature)} bytes")
        print(f"Signature CRC32: 0x{fw.signature_crc32:08X}")

def read_application_binary(path: str) -> bytes:
    _, ext = os.path.splitext(path.lower())
    if ext != ".bin":
        raise ValueError("Only raw .bin application images can be signed")

    with open(path, "rb") as f:
        data = f.read()

    if not data:
        raise ValueError("Input application binary is empty")

    return data

def build_signed_package(app_data: bytes, signature: bytes, app_id: int, signature_id: int) -> bytes:
    fw = FirmwareImage(app_data, signature=signature)
    app_header = struct.pack(SECTION_HEADER_FORMAT, app_id, fw.size, fw.crc32)
    sig_header = struct.pack(SECTION_HEADER_FORMAT, signature_id, len(signature), fw.signature_crc32)
    return app_header + app_data + sig_header + signature

def write_signed_package(args: argparse.Namespace) -> None:
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Firmware file not found: {args.input}")
    if not os.path.exists(args.private_key):
        raise FileNotFoundError(f"Private key file not found: {args.private_key}")

    app_data = read_application_binary(args.input)
    from firmware.signer import FirmwareSigner

    signer = FirmwareSigner(args.private_key)
    signature = signer.sign(app_data)
    package = build_signed_package(app_data, signature, args.app_id, args.signature_id)
    fw = FirmwareImage(app_data, signature=signature)

    with open(args.output, "wb") as f:
        f.write(package)

    if args.verbose:
        print(f"Input: {args.input}")
        print(f"Output: {args.output}")
        print(f"Application size: {fw.size} bytes")
        print(f"Application CRC32: 0x{fw.crc32:08X}")
        print(f"Signature size: {len(fw.signature)} bytes")
        print(f"Package size: {len(package)} bytes")

def main():
    parser = argparse.ArgumentParser(description="GachBoot Firmware Signer Utility")
    parser.add_argument("--input", help="Input application binary")
    parser.add_argument("--private-key", help="RSA-2048 private key PEM")
    parser.add_argument("--output", help="Output signed package")
    parser.add_argument("--app-id", type=parse_u16, default=0xA501, help="Application section ID")
    parser.add_argument("--signature-id", type=parse_u16, default=0x5A02, help="Signature section ID")
    parser.add_argument("--verbose", action="store_true", help="Print package details")
    parser.add_argument("--inspect", help="Inspect a signed package")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Sign command
    sign_parser = subparsers.add_parser("sign", help="Sign a firmware file")
    sign_parser.add_argument("firmware", help="Path to raw application firmware file (.bin)")
    sign_parser.add_argument("key", help="Path to RSA private key (.pem)")
    sign_parser.add_argument("--output", "-o", help="Output signed package path (default: <firmware>.signed.bin)")

    # Keygen command
    keygen_parser = subparsers.add_parser("keygen", help="Generate RSA-2048 key pair")
    keygen_parser.add_argument("--priv", default="private_key.pem", help="Private key output path")
    keygen_parser.add_argument("--pub", default="public_key.pem", help="Public key output path")

    args = parser.parse_args()

    if args.inspect:
        try:
            inspect_package(args.inspect)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    if args.input or args.private_key or args.output:
        if not args.input or not args.private_key or not args.output:
            parser.error("--input, --private-key, and --output are required together")
        try:
            write_signed_package(args)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    if args.command == "sign":
        if not os.path.exists(args.firmware):
            print(f"Error: Firmware file not found: {args.firmware}")
            sys.exit(1)

        if not os.path.exists(args.key):
            print(f"Error: Private key file not found: {args.key}")
            sys.exit(1)

        output_path = args.output if args.output else args.firmware + ".signed.bin"

        try:
            from firmware.signer import FirmwareSigner

            signer = FirmwareSigner(args.key)
            app_data = read_application_binary(args.firmware)
            signature = signer.sign(app_data)
            package = build_signed_package(app_data, signature, APP_SECTION_ID, SIGNATURE_SECTION_ID)

            with open(output_path, "wb") as f:
                f.write(package)
            print(f"Successfully signed {args.firmware}")
            print(f"Signed package saved to: {output_path}")

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "keygen":
        try:
            from firmware.signer import FirmwareSigner

            print(f"Generating RSA-2048 key pair...")
            FirmwareSigner.generate_keys(args.priv, args.pub)
            print(f"Private key: {args.priv}")
            print(f"Public key:  {args.pub}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
