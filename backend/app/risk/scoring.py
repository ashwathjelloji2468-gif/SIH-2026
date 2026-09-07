from typing import List, Dict, Any
from app.models.enums import RiskLevel, QuantumSafety

def get_risk_level_from_score(score: float) -> RiskLevel:
    """
    Deterministic Risk Level thresholds:
    - 0 to 24: LOW
    - 25 to 49: MODERATE
    - 50 to 74: HIGH
    - 75 to 100: CRITICAL
    """
    s = round(score, 1)
    if s >= 75.0:
        return RiskLevel.CRITICAL
    elif s >= 50.0:
        return RiskLevel.HIGH
    elif s >= 25.0:
        return RiskLevel.MODERATE
    else:
        return RiskLevel.LOW

def calculate_confidence_score(detector_names: List[str], evidence_count: int = 1) -> float:
    """
    Confidence is independent of risk score.
    Higher for direct AST/certificate evidence, lower for binary/container/unresolved.
    """
    if not detector_names:
        return 0.40

    detectors = [d.lower() for d in detector_names]
    max_conf = 0.40

    for d in detectors:
        if "sourcescanner" in d or "ast" in d or "apidetector" in d:
            max_conf = max(max_conf, 0.95)
        elif "certificatescanner" in d:
            max_conf = max(max_conf, 0.90)
        elif "dependencyscanner" in d:
            max_conf = max(max_conf, 0.80)
        elif "binaryscanner" in d:
            max_conf = max(max_conf, 0.60)
        elif "containerscanner" in d:
            max_conf = max(max_conf, 0.55)

    # Slight boost for multiple evidence items, max 1.0
    if evidence_count > 1:
        max_conf = min(1.0, max_conf + 0.05)

    return round(max_conf, 2)

def calculate_deterministic_risk_score(
    quantum_exposure: float,      # 30%
    data_sensitivity: float,      # 20%
    business_criticality: float,  # 15%
    migration_complexity: float,  # 15%
    lifetime_exposure: float      # 20%
) -> float:
    """
    Formula:
    risk_score = (quantum_exposure * 0.30)
               + (data_sensitivity * 0.20)
               + (business_criticality * 0.15)
               + (migration_complexity * 0.15)
               + (lifetime_exposure * 0.20)

    Clamped to 0-100, rounded to 1 decimal place.
    """
    score = (
        (quantum_exposure * 0.30) +
        (data_sensitivity * 0.20) +
        (business_criticality * 0.15) +
        (migration_complexity * 0.15) +
        (lifetime_exposure * 0.20)
    )
    return round(min(100.0, max(0.0, score)), 1)
