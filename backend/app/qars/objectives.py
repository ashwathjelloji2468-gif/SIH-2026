from typing import Optional, List, Any
from app.models.enums import CryptoPurpose
from app.risk.rules import determine_crypto_purpose
from app.knowledge.crypto_catalog import CRYPTO_CATALOG, evaluate_quantum_assessment
from app.qars.models import SecurityObjectiveResult

# Deterministic purpose-to-objectives mapping table
PURPOSE_OBJECTIVE_MAP = {
    CryptoPurpose.ENCRYPTION: ["confidentiality"],
    CryptoPurpose.KEY_ESTABLISHMENT: ["confidentiality", "key_establishment"],
    CryptoPurpose.SIGNATURE: ["integrity", "authentication"],
    CryptoPurpose.DIGITAL_SIGNATURE: ["integrity", "authentication"],
    CryptoPurpose.AUTHENTICATION: ["authentication"],
    CryptoPurpose.HASHING: ["integrity"],
    CryptoPurpose.MAC: ["integrity", "authentication"],
    CryptoPurpose.PASSWORD_DERIVATION: ["confidentiality"],
    CryptoPurpose.UNKNOWN: [],
}


def resolve_security_objectives(
    algorithm_name: str,
    purpose: Optional[Any] = None
) -> SecurityObjectiveResult:
    """
    Resolves normalized security objectives for an algorithm and purpose.
    Priority:
    1. Explicit purpose input
    2. Rule-based determine_crypto_purpose(algorithm_name)
    3. Knowledge-base algorithm purpose fallback
    4. UNKNOWN

    Allowed identifiers: confidentiality, integrity, authentication, key_establishment.
    """
    raw_name = (algorithm_name or "").strip()
    source = "UNKNOWN"
    resolved_purpose = CryptoPurpose.UNKNOWN

    # 1. Explicit purpose input check
    if purpose is not None:
        if isinstance(purpose, CryptoPurpose) and purpose != CryptoPurpose.UNKNOWN:
            resolved_purpose = purpose
            source = "EXPLICIT_PURPOSE"
        elif isinstance(purpose, str) and purpose.strip().upper() not in ["", "UNKNOWN"]:
            p_upper = purpose.strip().upper()
            try:
                resolved_purpose = CryptoPurpose[p_upper]
                source = "EXPLICIT_PURPOSE"
            except KeyError:
                # String matching fallback for custom purpose string
                for enum_item in CryptoPurpose:
                    if enum_item.name == p_upper or enum_item.value == p_upper:
                        resolved_purpose = enum_item
                        source = "EXPLICIT_PURPOSE"
                        break

    # 2. Rule-based determine_crypto_purpose if purpose still UNKNOWN
    if resolved_purpose == CryptoPurpose.UNKNOWN and raw_name:
        rule_purpose = determine_crypto_purpose(raw_name)
        if rule_purpose != CryptoPurpose.UNKNOWN:
            resolved_purpose = rule_purpose
            source = "DETERMINED_PURPOSE"

    # 3. Knowledge-base algorithm purpose fallback
    if resolved_purpose == CryptoPurpose.UNKNOWN and raw_name:
        assessment = evaluate_quantum_assessment(raw_name)
        canon_name = assessment.get("algorithm", raw_name).strip().upper()
        if canon_name in CRYPTO_CATALOG:
            entry_purposes = CRYPTO_CATALOG[canon_name].get("purposes", [])
            if entry_purposes:
                resolved_purpose = entry_purposes[0]
                source = "ALGORITHM_KNOWLEDGE_BASE"

    # Map purpose to list of security objectives (preserving deterministic ordering)
    objectives = PURPOSE_OBJECTIVE_MAP.get(resolved_purpose, [])

    return SecurityObjectiveResult(
        objectives=objectives,
        purpose_used=resolved_purpose.value if hasattr(resolved_purpose, "value") else str(resolved_purpose),
        source=source
    )
