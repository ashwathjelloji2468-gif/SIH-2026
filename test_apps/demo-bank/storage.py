import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt_bank_statement(data: bytes, key: bytes):
    # AES-GCM symmetric encryption
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext
