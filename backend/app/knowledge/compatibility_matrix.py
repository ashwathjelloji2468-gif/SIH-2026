from typing import Dict, Any

COMPATIBILITY_MATRIX: Dict[str, Dict[str, Any]] = {
    "RSA->ML-KEM": {
        "score": 0.85,
        "notes": "Direct replacement for key encapsulation; requires KEM API adaptation."
    },
    "RSA->ML-DSA": {
        "score": 0.80,
        "notes": "Requires handling larger signature size in headers/payloads."
    },
    "ECDSA->ML-DSA": {
        "score": 0.85,
        "notes": "Signature size increases from 64B to ~2.4KB."
    },
    "ECDH->ML-KEM": {
        "score": 0.90,
        "notes": "High compatibility in hybrid TLS protocol implementations."
    }
}
