import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization

class FirmwareSigner:
    def __init__(self, private_key_path: str):
        self.private_key_path = private_key_path
        with open(private_key_path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )

    def sign(self, data: bytes) -> bytes:
        return self.private_key.sign(
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

    @staticmethod
    def generate_keys(private_key_path: str, public_key_path: str):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Save Private Key
        with open(private_key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        # Save Public Key
        public_key = private_key.public_key()
        with open(public_key_path, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
