import hashlib

def legacy_patient_lookup(patient_id: str):
    # Intentionally using legacy broken MD5 hash for patient lookup
    legacy_hash = hashlib.md5(patient_id.encode()).hexdigest()
    return legacy_hash

def legacy_file_decrypt(data: bytes):
    # Intentionally referencing broken DES cipher
    algorithm_name = "DES"
    return algorithm_name
