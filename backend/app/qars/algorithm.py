import re
from typing import Optional, Dict, Any, Tuple
from app.qars.knowledge import (
    QuantumAlgorithmProfile,
    QARSKnowledgeResolver,
    map_attack_algorithm_to_family
)
from app.qars.objectives import resolve_security_objectives
from app.qars.models import QARSAlgorithmRisk
from app.knowledge.crypto_catalog import evaluate_quantum_assessment


def extract_parameterized_algorithm_details(
    algorithm_name: str,
    explicit_key_size: Optional[int] = None
) -> Tuple[str, Optional[int]]:
    """
    Parses parameterized algorithm strings (e.g. RSA-2048, ECDSA-P256, AES-256)
    into a canonical base algorithm name and key_size parameter.
    Does NOT assume every numeric substring is a key size (e.g. SHA-256 output bits).
    """
    if not algorithm_name or not str(algorithm_name).strip():
        return "UNKNOWN", explicit_key_size

    raw = str(algorithm_name).strip().upper()

    # Known base algorithm canonicalization
    if raw.startswith("RSA"):
        match = re.search(r"(\d{4})", raw)
        key_size = explicit_key_size or (int(match.group(1)) if match else None)
        return "RSA", key_size

    if "ECDSA" in raw or "SECP" in raw or "PRIME256" in raw:
        match = re.search(r"(256|384|521)", raw)
        key_size = explicit_key_size or (int(match.group(1)) if match else None)
        return "ECDSA", key_size

    if "ECDH" in raw or "X25519" in raw:
        match = re.search(r"(256|384|521)", raw)
        key_size = explicit_key_size or (int(match.group(1)) if match else (256 if "X25519" in raw else None))
        return "ECDH", key_size

    if raw.startswith("AES"):
        match = re.search(r"(128|192|256)", raw)
        key_size = explicit_key_size or (int(match.group(1)) if match else None)
        return "AES", key_size

    if "SHA" in raw:
        if "256" in raw:
            return "SHA-256", explicit_key_size
        elif "512" in raw:
            return "SHA-512", explicit_key_size
        elif "384" in raw:
            return "SHA-384", explicit_key_size
        elif "1" in raw and "512" not in raw and "256" not in raw:
            return "SHA-1", explicit_key_size
        return "SHA-256", explicit_key_size

    if raw.startswith("MD5"):
        return "MD5", explicit_key_size

    if raw.startswith("DES") or raw.startswith("3DES"):
        return "DES", explicit_key_size

    # Fallback to catalog assessment algorithm name
    assessment = evaluate_quantum_assessment(raw, key_size=explicit_key_size)
    canonical = assessment.get("algorithm", raw).upper()
    return canonical, explicit_key_size


def resolve_algorithm_profile(
    algorithm_name: str,
    key_size: Optional[int] = None,
    purpose: Optional[str] = None,
    calibration_data: Optional[Dict[str, Dict[str, float]]] = None
) -> QuantumAlgorithmProfile:
    """
    Resolves canonical QuantumAlgorithmProfile using QARSKnowledgeResolver.
    """
    canonical_name, effective_key_size = extract_parameterized_algorithm_details(algorithm_name, key_size)
    resolver = QARSKnowledgeResolver()
    profile = resolver.resolve_profile(
        canonical_name,
        key_size=effective_key_size,
        purpose=purpose,
        calibration_data=calibration_data
    )

    # Attach security objectives
    obj_res = resolve_security_objectives(algorithm_name, purpose=purpose)
    profile.security_objectives = obj_res.objectives

    return profile


def evaluate_algorithm_risk(
    algorithm_name: str,
    key_size: Optional[int] = None,
    purpose: Optional[str] = None,
    calibration_data: Optional[Dict[str, Dict[str, float]]] = None
) -> QARSAlgorithmRisk:
    """
    Evaluates Phase 2 Algorithm-Specific Quantum Risk (AQR).
    Formula: AQR = Va * Sp (clamped [0..1])
    Only calculated when both Va and Sp are explicitly configured in calibration_data.
    Otherwise returns calibration_status = 'UNCONFIGURED' and aqr_score = None without
    inventing numeric defaults.
    """
    if not algorithm_name or not str(algorithm_name).strip() or str(algorithm_name).strip().upper() in ["UNKNOWN", "NONE"]:
        obj_res = resolve_security_objectives(algorithm_name, purpose=purpose)
        return QARSAlgorithmRisk(
            algorithm=algorithm_name or "UNKNOWN",
            canonical_algorithm="UNKNOWN",
            attack_family="UNKNOWN",
            vulnerability_factor=None,
            security_strength_factor=None,
            aqr_score=None,
            calibration_status="UNCONFIGURED",
            confidence="INSUFFICIENT_EVIDENCE",
            quantum_attack="None",
            explanation="Algorithm is not sufficiently represented in the QARS knowledge base.",
            security_objectives=obj_res.objectives
        )

    raw_name = str(algorithm_name).strip()
    profile = resolve_algorithm_profile(raw_name, key_size=key_size, purpose=purpose, calibration_data=calibration_data)
    obj_res = resolve_security_objectives(raw_name, purpose=purpose)

    assessment = evaluate_quantum_assessment(raw_name, key_size=key_size)
    quantum_attack = assessment.get("attack_algorithm", "Unknown Attack")

    va = profile.vulnerability_factor
    sp = profile.security_strength_factor

    if va is not None and sp is not None:
        aqr = min(1.0, max(0.0, float(va) * float(sp)))
        calib_status = "CONFIGURED"
        explanation = (
            f"AQR calculated as Va ({va}) * Sp ({sp}) = {aqr:.4f} for algorithm '{profile.canonical_name}'. "
            f"Attack family {profile.attack_family} is derived from the cryptographic knowledge base; "
            f"Va/Sp numeric factors are supplied by {profile.calibration_version}."
        )
    else:
        aqr = None
        calib_status = "UNCONFIGURED"
        missing = []
        if va is None:
            missing.append("vulnerability_factor (Va)")
        if sp is None:
            missing.append("security_strength_factor (Sp)")
        explanation = f"Calibration data missing for algorithm '{profile.canonical_name}': {', '.join(missing)} unconfigured."

    return QARSAlgorithmRisk(
        algorithm=raw_name,
        canonical_algorithm=profile.canonical_name,
        attack_family=profile.attack_family,
        vulnerability_factor=va,
        security_strength_factor=sp,
        aqr_score=aqr,
        calibration_status=calib_status,
        confidence=profile.confidence,
        quantum_attack=quantum_attack,
        explanation=explanation,
        security_objectives=obj_res.objectives,
        calibration_version=profile.calibration_version,
        calibration_source=profile.calibration_source,
        calibration_methodology=profile.calibration_methodology,
        calibration_confidence=profile.calibration_confidence,
    )
