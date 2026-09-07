import re
from typing import Tuple, Dict, Any, List
from app.models.enums import QuantumSafety, CryptoPurpose

# 1. Deterministic Quantum Vulnerability Classification
VULNERABLE_PUBLIC_KEY_PATTERNS = [
    r"^RSA", r"^DSA", r"^DH", r"^DIFFIE-HELLMAN", r"^ECDH", r"^ECDSA", r"^EC", r"^ECC",
    r"^ED25519", r"^ED448", r"^X25519", r"^X448", r"^ELGAMAL", r"^ELLIPTIC"
]

REDUCED_MARGIN_PATTERNS = [
    r"^AES", r"^CHACHA", r"^CHACHA20", r"^SALSA", r"^SHA", r"^SHA1", r"^SHA2", r"^SHA3",
    r"^HMAC", r"^BLAKE", r"^RIPEMD"
]

PASSWORD_DERIVATION_PATTERNS = [
    r"^PBKDF2", r"^ARGON2", r"^BCRYPT", r"^SCRYPT"
]

def classify_algorithm_vulnerability(algorithm_name: str) -> Tuple[QuantumSafety, float, str]:
    """
    Returns (QuantumSafety, quantum_exposure_score (0-100), rationale)
    - QUANTUM_VULNERABLE: 100
    - UNKNOWN: 50
    - QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN: 30
    - NOT_DIRECTLY_QUANTUM_VULNERABLE: 10
    """
    if not algorithm_name or algorithm_name.upper() in ["UNKNOWN", "NONE"]:
        return (QuantumSafety.UNKNOWN, 50.0, "Algorithm is unknown or unspecified.")

    alg_upper = algorithm_name.strip().upper()

    for pattern in VULNERABLE_PUBLIC_KEY_PATTERNS:
        if re.search(pattern, alg_upper):
            return (
                QuantumSafety.QUANTUM_VULNERABLE,
                100.0,
                f"'{algorithm_name}' is a classical public-key algorithm vulnerable to Shor's algorithm on quantum computers."
            )

    for pattern in REDUCED_MARGIN_PATTERNS:
        if re.search(pattern, alg_upper):
            return (
                QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN,
                30.0,
                f"'{algorithm_name}' is symmetric/hashing crypto. Grover's algorithm reduces effective security margin but does not break it completely."
            )

    for pattern in PASSWORD_DERIVATION_PATTERNS:
        if re.search(pattern, alg_upper):
            return (
                QuantumSafety.NOT_DIRECTLY_QUANTUM_VULNERABLE,
                10.0,
                f"'{algorithm_name}' is a password key derivation function and not directly vulnerable to quantum speedup."
            )

    return (QuantumSafety.UNKNOWN, 50.0, f"'{algorithm_name}' could not be definitively classified.")


# 2. Crypto Purpose Mapping
def determine_crypto_purpose(algorithm_name: str, current_purpose: CryptoPurpose = None) -> CryptoPurpose:
    if current_purpose and current_purpose != CryptoPurpose.UNKNOWN:
        return current_purpose

    alg_upper = (algorithm_name or "").strip().upper()
    if any(k in alg_upper for k in ["ECDSA", "RSA-PSS", "ED25519", "ED448", "DSA", "SIGN"]):
        return CryptoPurpose.DIGITAL_SIGNATURE
    elif any(k in alg_upper for k in ["ECDH", "DH", "DIFFIE", "X25519", "X448", "KEM"]):
        return CryptoPurpose.KEY_ESTABLISHMENT
    elif any(k in alg_upper for k in ["AES", "CHACHA", "SALSA", "DES", "3DES", "CIPHER"]):
        return CryptoPurpose.ENCRYPTION
    elif any(k in alg_upper for k in ["SHA", "MD5", "BLAKE", "RIPEMD", "HASH"]):
        return CryptoPurpose.HASHING
    elif "HMAC" in alg_upper:
        return CryptoPurpose.MAC
    elif any(k in alg_upper for k in ["PBKDF2", "ARGON2", "BCRYPT", "SCRYPT"]):
        return CryptoPurpose.PASSWORD_DERIVATION

    return CryptoPurpose.UNKNOWN


# 3. Data Sensitivity Mapping
SENSITIVITY_SCORES: Dict[str, float] = {
    "PUBLIC": 20.0,
    "INTERNAL": 40.0,
    "CONFIDENTIAL": 60.0,
    "RESTRICTED": 80.0,
    "CRITICAL": 100.0,
    "UNKNOWN": 60.0
}

def get_sensitivity_score(label: str = "UNKNOWN") -> float:
    return SENSITIVITY_SCORES.get((label or "UNKNOWN").upper(), 60.0)


# 4. Business Criticality Mapping
CRITICALITY_SCORES: Dict[str, float] = {
    "LOW": 25.0,
    "MEDIUM": 50.0,
    "HIGH": 75.0,
    "CRITICAL": 100.0,
    "UNKNOWN": 50.0
}

def get_criticality_score(label: str = "UNKNOWN") -> float:
    return CRITICALITY_SCORES.get((label or "UNKNOWN").upper(), 50.0)


# 5. Migration Complexity Mapping
def get_migration_complexity_score(asset_type: str, detector_names: List[str]) -> Tuple[float, str]:
    """
    Calculates migration complexity score (0-100) based on asset metadata and evidence detectors.
    - LOW (25): simple software crypto usage
    - MEDIUM (50): dependency / API reference
    - HIGH (75-100): binary/native dependency, certificate chains, container infrastructure
    """
    detectors = [d.lower() for d in (detector_names or [])]
    atype = (asset_type or "").upper()

    if atype == "BINARY" or "binaryscanner" in detectors:
        return (90.0, "HIGH: Native binary dependency requiring compiled source refactoring and re-linking.")
    elif atype == "CONTAINER" or "containerscanner" in detectors:
        return (80.0, "HIGH: Container base image or infrastructure manifest modification required.")
    elif atype == "CERTIFICATE" or "certificatescanner" in detectors:
        return (75.0, "HIGH: Requires PKI certificate re-issuance and trust store updating.")
    elif atype == "DEPENDENCY" or "dependencyscanner" in detectors:
        return (50.0, "MEDIUM: Third-party library dependency update or replacement needed.")
    elif atype in ["ALGORITHM", "API_CALL"] or "sourcescanner" in detectors:
        return (25.0, "LOW: Source-level API call update in application code.")

    return (50.0, "MEDIUM: Standard cryptographic asset migration complexity.")


# 6. Lifetime Exposure Score
def get_lifetime_exposure_score(
    data_lifetime_years: float,
    migration_time_years: float,
    quantum_threat_horizon_year: int,
    current_year: int = 2026
) -> Tuple[float, str]:
    """
    Calculates lifetime exposure subscore (0-100) based on protection window vs quantum threat horizon.
    """
    remaining_years = max(1.0, float(quantum_threat_horizon_year - current_year))
    protection_window = float(data_lifetime_years + migration_time_years)

    ratio = protection_window / remaining_years

    if ratio >= 1.5:
        return (100.0, f"Critical lifetime exposure: Protection window ({protection_window}y) far exceeds threat horizon ({remaining_years}y).")
    elif ratio > 1.0:
        return (80.0, f"High lifetime exposure: Protection window ({protection_window}y) exceeds threat horizon ({remaining_years}y).")
    elif ratio > 0.7:
        return (50.0, f"Moderate lifetime exposure: Protection window ({protection_window}y) approaches threat horizon ({remaining_years}y).")
    else:
        return (20.0, f"Low lifetime exposure: Protection window ({protection_window}y) comfortably fits within threat horizon ({remaining_years}y).")
