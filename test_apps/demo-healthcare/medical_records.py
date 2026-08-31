import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def protect_patient_record(patient_data: bytes, key: bytes):
    # AES-GCM encryption for HIPAA compliance
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    encrypted = aesgcm.encrypt(nonce, patient_data, None)
    
    # SHA-256 integrity hash
    data_hash = hashlib.sha256(patient_data).hexdigest()
    return encrypted, data_hash
