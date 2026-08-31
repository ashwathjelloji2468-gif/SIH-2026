from typing import Dict, Any
from app.models.enums import CryptoPurpose, StandardStatus

CRYPTO_CATALOG: Dict[str, Dict[str, Any]] = {
    "RSA": {
        "family": "Asymmetric",
        "quantum_vulnerable": True,
        "purposes": [CryptoPurpose.SIGNATURE, CryptoPurpose.KEY_ESTABLISHMENT, CryptoPurpose.ENCRYPTION],
        "status": StandardStatus.FINAL_STANDARD,
        "default_key_sizes": [2048, 3072, 4096]
    },
    "ECDSA": {
        "family": "Asymmetric",
        "quantum_vulnerable": True,
        "purposes": [CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION],
        "status": StandardStatus.FINAL_STANDARD,
        "default_key_sizes": [256, 384, 521]
    },
    "ECDH": {
        "family": "Asymmetric",
        "quantum_vulnerable": True,
        "purposes": [CryptoPurpose.KEY_ESTABLISHMENT],
        "status": StandardStatus.FINAL_STANDARD,
        "default_key_sizes": [256, 384, 521]
    },
    "AES": {
        "family": "Symmetric",
        "quantum_vulnerable": False,  # AES-256 is quantum resistant
        "purposes": [CryptoPurpose.ENCRYPTION],
        "status": StandardStatus.FINAL_STANDARD,
        "default_key_sizes": [128, 192, 256]
    },
    "SHA-256": {
        "family": "Hash",
        "quantum_vulnerable": False,
        "purposes": [CryptoPurpose.HASHING],
        "status": StandardStatus.FINAL_STANDARD,
        "default_key_sizes": []
    },
    "MD5": {
        "family": "Hash",
        "quantum_vulnerable": True,  # Broken classically and quantum
        "purposes": [CryptoPurpose.HASHING],
        "status": StandardStatus.RESEARCH_NON_STANDARD,
        "default_key_sizes": []
    },
    "DES": {
        "family": "Symmetric",
        "quantum_vulnerable": True,
        "purposes": [CryptoPurpose.ENCRYPTION],
        "status": StandardStatus.RESEARCH_NON_STANDARD,
        "default_key_sizes": [56]
    }
}
