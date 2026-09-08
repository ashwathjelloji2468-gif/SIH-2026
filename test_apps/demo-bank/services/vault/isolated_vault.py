import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt_bank_statement(data: bytes, key: bytes):
    """
    Isolated AES-256 symmetric encryption primitive used only within vault component.
    Fan-in = 1 (Low Blast Radius).
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext
