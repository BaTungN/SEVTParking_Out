
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from  cryptography.hazmat.primitives import hashes,serialization
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import json, base64
import hashlib
from Crypto.Random import get_random_bytes
class AESUtil:
    def __init__(self, key: bytes):
        self.key = key  # key ph?i l� 16/24/32 bytes (AES-128/192/256)

    def encrypt(self, plaintext: str) -> bytes:
        iv = get_random_bytes(16)  # IV = 16 bytes
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))

        # G?p iv + ciphertext
        return iv + ciphertext

    def decrypt(self, iv_and_cipher: bytes) -> str:
        iv = iv_and_cipher[:16]
        ciphertext = iv_and_cipher[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted.decode('utf-8')


# T?o key aes luu v�o file
def generate_aes_key_iv():
    key = get_random_bytes(32)  # 256-bit key
    iv = get_random_bytes(16)  # 128-bit IV

    # save as base64 for easy cross-platform use
    data = {
        'key': base64.b64encode(key).decode()
    }

    with open('aes_key_iv.json', 'w') as f:
        json.dump(data, f)

    print("AES key + IV generated and saved.")

# generate_aes_key_iv()

# Load key
def load_aes_key_iv():
    with open('aes_key_iv.json') as f:
        data = json.load(f)
    key = base64.b64decode(data['key'])
    iv = base64.b64decode(data['iv'])
    return key, iv
class AsymmetricEncryption:

    @staticmethod
    def generate_key():
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        # Export keys to PEM format (as string)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        return private_key, public_key

    @staticmethod
    def encrypt(public_key_str, data_to_encrypt):
        public_key = serialization.load_pem_public_key(public_key_str.encode())
        encrypted = public_key.encrypt(
            data_to_encrypt.encode(),
            padding.PKCS1v15()
        )
        return encrypted

    @staticmethod
    def decrypt(private_key_str, encrypted_bytes):
        private_key = serialization.load_pem_private_key(private_key_str.encode(), password=None)
        decrypted = private_key.decrypt(
            encrypted_bytes,
            padding.PKCS1v15()
        )
        return decrypted.decode()

    @staticmethod
    def sign(private_key_str, data_to_sign):
        private_key = serialization.load_pem_private_key(private_key_str.encode(), password=None)
        signature = private_key.sign(
            data_to_sign.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return signature

    @staticmethod
    def verify(public_key_str, data, signature):
        public_key = serialization.load_pem_public_key(public_key_str.encode())
        try:
            public_key.verify(
                signature,
                data.encode(),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False

    @staticmethod
    def hash_sha256(data: str) -> bytes:
        return hashlib.sha256(data.encode('utf-8')).digest()
if __name__ == '__main__':
    public_key=None
    private_key=None
