from typing import Dict, Any, Tuple, Optional
from app.models.enums import AssetType, CryptoPurpose, QuantumSafety
from app.knowledge.crypto_catalog import CRYPTO_CATALOG, evaluate_quantum_assessment


def determine_quantum_safety(algorithm_name: str, key_size: Optional[int] = None) -> QuantumSafety:
    if not algorithm_name or not str(algorithm_name).strip():
        return QuantumSafety.UNKNOWN

    assessment = evaluate_quantum_assessment(algorithm_name, key_size)
    q_status = assessment.get("quantum_status")

    if q_status in ["CRITICAL", "VULNERABLE", "HIGH"]:
        return QuantumSafety.QUANTUM_VULNERABLE
    elif q_status in ["PARAMETER_DEPENDENT", "MODERATE"]:
        return QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN
    elif q_status == "LOW":
        return QuantumSafety.QUANTUM_SAFE
    elif q_status == "UNKNOWN":
        return QuantumSafety.UNKNOWN

    return QuantumSafety.UNKNOWN



def determine_asset_lifetime(
    algorithm_name: str,
    asset_type: Any = AssetType.ALGORITHM,
    purpose: Optional[CryptoPurpose] = None
) -> Tuple[float, str]:
    """Classify data lifetime (shelf-life) for a cryptographic artefact.

    Returns (data_lifetime_years, lifetime_label):
    - SHORT_TERM (<= 3.0 years): session keys, ephemeral TLS, short-lived tokens, HMACs
    - MEDIUM_TERM (5.0-7.0 years): standard symmetric data encryption, application tokens
    - LONG_TERM (10.0 years): digital signatures, code signing, certificates, PKI, RSA keys
    - PERMANENT (20.0 years): root certificates, master keys, vendor managed hardware/binaries
    """
    alg_upper = (algorithm_name or "").strip().upper()
    atype = asset_type.value if hasattr(asset_type, "value") else str(asset_type)

    if atype in ["VENDOR_MANAGED", "BINARY"] or "ROOT" in alg_upper:
        return (20.0, "PERMANENT")

    if atype == "CERTIFICATE" or purpose in [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE]:
        return (10.0, "LONG_TERM")

    if any(k in alg_upper for k in ["RSA", "ECDSA", "ED25519", "DSA"]):
        return (10.0, "LONG_TERM")

    if atype == "PROTOCOL" or purpose == CryptoPurpose.AUTHENTICATION or "SESSION" in alg_upper:
        return (2.0, "SHORT_TERM")

    if purpose in [CryptoPurpose.HASHING, CryptoPurpose.MAC]:
        return (3.0, "SHORT_TERM")

    if any(k in alg_upper for k in ["AES", "CHACHA", "ENCRYPTION"]):
        return (7.0, "MEDIUM_TERM")

    return (10.0, "LONG_TERM")


def determine_business_criticality(
    algorithm_name: str,
    asset_type: Any = AssetType.ALGORITHM,
    purpose: Optional[CryptoPurpose] = None,
    quantum_safety: Optional[QuantumSafety] = None
) -> Tuple[str, float]:
    """Classify business criticality for a cryptographic artefact.

    Returns (criticality_label, criticality_score):
    - CRITICAL (100.0): Quantum vulnerable asymmetric keys, root certificates, vendor managed binaries
    - HIGH (75.0): Primary encryption, PQC transition algorithms, key exchange protocols
    - MEDIUM (50.0): Standard hashing, third-party dependencies, API calls
    - LOW (25.0): Utility hashing, internal helpers
    """
    alg_upper = (algorithm_name or "").strip().upper()
    atype = asset_type.value if hasattr(asset_type, "value") else str(asset_type)
    qs = quantum_safety or determine_quantum_safety(algorithm_name)

    if atype in ["VENDOR_MANAGED", "BINARY"] or (qs == QuantumSafety.QUANTUM_VULNERABLE and "RSA" in alg_upper):
        return ("CRITICAL", 100.0)

    if atype == "CERTIFICATE" or qs == QuantumSafety.QUANTUM_VULNERABLE or purpose == CryptoPurpose.KEY_ESTABLISHMENT:
        return ("HIGH", 75.0)

    if atype in ["DEPENDENCY", "PROTOCOL"] or purpose in [CryptoPurpose.ENCRYPTION, CryptoPurpose.DIGITAL_SIGNATURE]:
        return ("MEDIUM", 50.0)

    if purpose in [CryptoPurpose.HASHING, CryptoPurpose.PASSWORD_DERIVATION]:
        return ("LOW", 25.0)

    return ("MEDIUM", 50.0)


def classify_crypto_asset(
    algorithm_name: str,
    key_size: Optional[int] = None,
    asset_type: Any = AssetType.ALGORITHM,
    purpose: Optional[CryptoPurpose] = None,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Unified Classification function for cryptographic artefacts.

    Classifies every artefact by Type, Lifetime, and Business Criticality.
    """
    qs = determine_quantum_safety(algorithm_name, key_size)
    lifetime_years, lifetime_label = determine_asset_lifetime(algorithm_name, asset_type, purpose)
    criticality_label, criticality_score = determine_business_criticality(algorithm_name, asset_type, purpose, qs)

    atype_str = asset_type.value if hasattr(asset_type, "value") else str(asset_type)
    summary = f"Type: {atype_str} | Lifetime: {lifetime_label} ({lifetime_years}y) | Criticality: {criticality_label} ({criticality_score})"

    return {
        "asset_type": asset_type,
        "purpose": purpose or CryptoPurpose.UNKNOWN,
        "quantum_safety": qs,
        "data_lifetime_years": lifetime_years,
        "lifetime_label": lifetime_label,
        "business_criticality_label": criticality_label,
        "business_criticality_score": criticality_score,
        "classification_summary": summary,
    }
