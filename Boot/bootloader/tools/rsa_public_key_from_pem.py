#!/usr/bin/env python3
"""Generate bootloader RSA-2048 public key macros from a PEM public key."""

from __future__ import annotations

import argparse
import base64
from pathlib import Path


RSA_WORD_COUNT = 64
RSA_BITS = 2048
RSA_EXPONENT = 65537


class DerReader:
    """Small DER reader for RSA public key structures."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._offset = 0

    def read_tlv(self) -> tuple[int, bytes]:
        if self._offset >= len(self._data):
            raise ValueError("Unexpected end of DER data")

        tag = self._data[self._offset]
        self._offset += 1
        length = self._read_length()
        end = self._offset + length

        if end > len(self._data):
            raise ValueError("DER length exceeds input size")

        value = self._data[self._offset:end]
        self._offset = end
        return tag, value

    def remaining(self) -> int:
        return len(self._data) - self._offset

    def _read_length(self) -> int:
        if self._offset >= len(self._data):
            raise ValueError("Missing DER length")

        first = self._data[self._offset]
        self._offset += 1

        if (first & 0x80) == 0:
            return first

        count = first & 0x7F
        if count == 0 or count > 4:
            raise ValueError("Unsupported DER length encoding")

        if (self._offset + count) > len(self._data):
            raise ValueError("Truncated DER length")

        length = 0
        for _ in range(count):
            length = (length << 8) | self._data[self._offset]
            self._offset += 1

        return length


def read_pem_body(path: Path) -> bytes:
    lines = path.read_text(encoding="ascii").splitlines()
    body: list[str] = []
    inside = False

    for line in lines:
        if line.startswith("-----BEGIN "):
            inside = True
            continue
        if line.startswith("-----END "):
            break
        if inside:
            body.append(line.strip())

    if not body:
        raise ValueError("PEM body not found")

    return base64.b64decode("".join(body), validate=True)


def read_integer(data: bytes) -> int:
    if len(data) == 0:
        raise ValueError("Empty INTEGER")
    if data[0] == 0:
        data = data[1:]
    return int.from_bytes(data, byteorder="big", signed=False)


def parse_pkcs1_public_key(der: bytes) -> tuple[int, int]:
    reader = DerReader(der)
    tag, sequence = reader.read_tlv()
    if tag != 0x30 or reader.remaining() != 0:
        raise ValueError("Expected DER SEQUENCE")

    seq = DerReader(sequence)
    tag, modulus = seq.read_tlv()
    if tag != 0x02:
        raise ValueError("Expected RSA modulus INTEGER")

    tag, exponent = seq.read_tlv()
    if tag != 0x02 or seq.remaining() != 0:
        raise ValueError("Expected RSA exponent INTEGER")

    return read_integer(modulus), read_integer(exponent)


def parse_spki_public_key(der: bytes) -> tuple[int, int]:
    reader = DerReader(der)
    tag, sequence = reader.read_tlv()
    if tag != 0x30 or reader.remaining() != 0:
        raise ValueError("Expected SubjectPublicKeyInfo SEQUENCE")

    seq = DerReader(sequence)
    tag, _algorithm = seq.read_tlv()
    if tag != 0x30:
        raise ValueError("Expected algorithm SEQUENCE")

    tag, bit_string = seq.read_tlv()
    if tag != 0x03 or seq.remaining() != 0:
        raise ValueError("Expected subjectPublicKey BIT STRING")

    if len(bit_string) < 2 or bit_string[0] != 0:
        raise ValueError("Unsupported BIT STRING encoding")

    return parse_pkcs1_public_key(bit_string[1:])


def parse_public_key(path: Path) -> tuple[int, int]:
    der = read_pem_body(path)

    try:
        return parse_spki_public_key(der)
    except ValueError:
        return parse_pkcs1_public_key(der)


def to_words_le(value: int) -> list[int]:
    words: list[int] = []

    for _ in range(RSA_WORD_COUNT):
        words.append(value & 0xFFFFFFFF)
        value >>= 32

    if value != 0:
        raise ValueError("Integer does not fit RSA-2048 word count")

    return words


def format_words(words: list[int]) -> str:
    lines: list[str] = []

    for index in range(0, len(words), 4):
        line_words = words[index:index + 4]
        lines.append("    " + ", ".join(f"0x{word:08X}u" for word in line_words))

    return ", \\\n".join(lines)


def write_header(path: Path, modulus: int, exponent: int) -> None:
    if exponent != RSA_EXPONENT:
        raise ValueError("Only RSA public exponent 65537 is supported")
    if modulus.bit_length() != RSA_BITS:
        raise ValueError("Only RSA-2048 public keys are supported")

    modulus_words = to_words_le(modulus)
    rr_words = to_words_le(pow(2, RSA_BITS * 2, modulus))
    n0inv = (-pow(modulus_words[0], -1, 1 << 32)) & 0xFFFFFFFF

    content = (
        "#ifndef BL_RSA_PUBLIC_KEY_GENERATED_H\n"
        "#define BL_RSA_PUBLIC_KEY_GENERATED_H\n\n"
        f"#define BL_RSA_PUBLIC_KEY_N0INV          0x{n0inv:08X}u\n\n"
        "#define BL_RSA_PUBLIC_KEY_N_WORDS \\\n"
        "{ \\\n"
        f"{format_words(modulus_words)} \\\n"
        "}\n\n"
        "#define BL_RSA_PUBLIC_KEY_RR_WORDS \\\n"
        "{ \\\n"
        f"{format_words(rr_words)} \\\n"
        "}\n\n"
        "#endif /* BL_RSA_PUBLIC_KEY_GENERATED_H */\n"
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pem", required=True, type=Path, help="RSA-2048 public key PEM")
    parser.add_argument("--out", required=True, type=Path, help="Generated C header path")
    args = parser.parse_args()

    modulus, exponent = parse_public_key(args.pem)
    write_header(args.out, modulus, exponent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
