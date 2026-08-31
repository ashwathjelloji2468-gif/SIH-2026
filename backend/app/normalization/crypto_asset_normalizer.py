from app.models.enums import QuantumSafety
from app.knowledge.crypto_catalog import CRYPTO_CATALOG

def determine_quantum_safety(algorithm_name: str, key_size: int = None) -> QuantumSafety:
    alg_upper = algorithm_name.upper()

    if alg_upper in ["RSA", "ECDSA", "ECDH", "MD5", "DES", "DSA", "DH"]:
        return QuantumSafety.QUANTUM_VULNERABLE

    if alg_upper in ["ML-KEM", "ML-DSA", "SLH-DSA"]:
        return QuantumSafety.QUANTUM_SAFE

    if alg_upper == "AES":
        if key_size and key_size < 256:
            return QuantumSafety.QUANTUM_VULNERABLE
        return QuantumSafety.QUANTUM_SAFE

    if alg_upper in ["SHA-256", "SHA-384", "SHA-512", "SHA3-256"]:
        return QuantumSafety.QUANTUM_SAFE

    info = CRYPTO_CATALOG.get(alg_upper)
    if info:
        return QuantumSafety.QUANTUM_VULNERABLE if info.get("quantum_vulnerable") else QuantumSafety.QUANTUM_SAFE

    return QuantumSafety.UNKNOWN
