from typing import Dict, Any, List
from app.models.enums import CryptoPurpose, StandardStatus

PQC_CATALOG: Dict[str, Dict[str, Any]] = {
    "ML-KEM": {
        "standard_code": "FIPS 203",
        "full_name": "Module-Lattice-Based Key-Encapsulation Mechanism",
        "purposes": [CryptoPurpose.KEY_ESTABLISHMENT, CryptoPurpose.ENCRYPTION],
        "status": StandardStatus.FINAL_STANDARD,
        "variants": ["ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"],
        "key_size_notes": "Public key size: 800 - 1568 bytes; Ciphertext size: 768 - 1568 bytes.",
        "performance_notes": "Fast key generation and encapsulation; larger public key size compared to RSA/ECC."
    },
    "ML-DSA": {
        "standard_code": "FIPS 204",
        "full_name": "Module-Lattice-Based Digital Signature Algorithm",
        "purposes": [CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION],
        "status": StandardStatus.FINAL_STANDARD,
        "variants": ["ML-DSA-44", "ML-DSA-65", "ML-DSA-87"],
        "key_size_notes": "Public key size: 1312 - 2592 bytes; Signature size: 2420 - 4627 bytes.",
        "performance_notes": "High verification performance; signature size significantly larger than RSA-2048."
    },
    "SLH-DSA": {
        "standard_code": "FIPS 205",
        "full_name": "Stateless Hash-Based Digital Signature Algorithm",
        "purposes": [CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION],
        "status": StandardStatus.FINAL_STANDARD,
        "variants": ["SLH-DSA-SHA2-128f", "SLH-DSA-SHAKE-128f", "SLH-DSA-SHA2-256f"],
        "key_size_notes": "Public key size: 32 - 64 bytes; Signature size: 7856 - 49856 bytes.",
        "performance_notes": "Conservative security relying solely on cryptographic hash functions; larger signature overhead."
    }
}
