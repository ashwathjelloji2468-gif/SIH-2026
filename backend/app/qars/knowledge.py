from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.knowledge.crypto_catalog import CRYPTO_CATALOG, evaluate_quantum_assessment
from app.qars.calibration import get_default_calibration_provider


class QuantumAlgorithmProfile(BaseModel):
    """
    QARS Quantum Algorithm Profile structure.
    Represents algorithm properties, attack family, and calibration status.
    """
    canonical_name: str
    aliases: List[str] = Field(default_factory=list)
    attack_family: str = Field("UNKNOWN", description="SHOR | GROVER | BHT | NONE | UNKNOWN")
    quantum_vulnerability_class: str = "UNKNOWN"
    vulnerability_factor: Optional[float] = Field(None, description="Va [0..1]")
    security_strength_factor: Optional[float] = Field(None, description="Sp [0..1]")
    security_objectives: List[str] = Field(default_factory=list)
    calibration_status: str = Field("UNCONFIGURED", description="CONFIGURED | UNCONFIGURED")
    source: str = "QARS_KNOWLEDGE_BASE"
    confidence: str = "INSUFFICIENT_EVIDENCE"
    calibration_version: str = "SENTRIQ QARS Prototype Heuristic Calibration v1"
    calibration_source: str = "SENTRIQ_PROTOTYPE_HEURISTIC"
    calibration_methodology: str = ""
    calibration_confidence: str = "INSUFFICIENT_EVIDENCE"


def map_attack_algorithm_to_family(attack_str: str) -> str:
    """
    Maps a raw attack algorithm description to standard QARS attack family.
    Allowed values: SHOR, GROVER, BHT, NONE, UNKNOWN.
    """
    if not attack_str or attack_str == "None":
        return "NONE"

    text = attack_str.upper()
    if "SHOR" in text:
        return "SHOR"
    elif "GROVER" in text and "BHT" in text:
        return "BHT"
    elif "BHT" in text:
        return "BHT"
    elif "GROVER" in text:
        return "GROVER"
    elif "NONE" in text or "NO IMMEDIATE" in text:
        return "NONE"
    else:
        return "UNKNOWN"


class QARSKnowledgeResolver:
    """
    Adapter/Resolver over SENTRIQ's CryptoCatalog and QARSCalibrationProvider.
    Resolves canonical algorithm profiles and applies versioned prototype heuristic calibration records.
    Does NOT invent or hardcode application-level Va/Sp numeric defaults in Python logic.
    """
    def __init__(self, catalog: Optional[Dict[str, Dict[str, Any]]] = None):
        self.catalog = catalog or CRYPTO_CATALOG

    def resolve_profile(
        self,
        algorithm_name: str,
        key_size: Optional[int] = None,
        purpose: Optional[str] = None,
        calibration_data: Optional[Dict[str, Dict[str, float]]] = None
    ) -> QuantumAlgorithmProfile:
        if not algorithm_name or not str(algorithm_name).strip() or str(algorithm_name).strip().upper() in ["UNKNOWN", "NONE"]:
            return QuantumAlgorithmProfile(
                canonical_name="UNKNOWN",
                aliases=[],
                attack_family="UNKNOWN",
                quantum_vulnerability_class="UNKNOWN",
                vulnerability_factor=None,
                security_strength_factor=None,
                security_objectives=[],
                calibration_status="UNCONFIGURED",
                source="QARS_KNOWLEDGE_BASE",
                confidence="INSUFFICIENT_EVIDENCE",
                calibration_version="SENTRIQ QARS Prototype Heuristic Calibration v1",
                calibration_source="SENTRIQ_PROTOTYPE_HEURISTIC",
                calibration_methodology="Algorithm unidentified or missing.",
                calibration_confidence="INSUFFICIENT_EVIDENCE"
            )

        raw_name = str(algorithm_name).strip()
        assessment = evaluate_quantum_assessment(raw_name, key_size=key_size)

        # Map canonical algorithm name from catalog or evaluation
        canonical_name = assessment.get("algorithm", raw_name).strip().upper()

        # Handle aliases and family matching
        if canonical_name in self.catalog:
            entry = self.catalog[canonical_name]
            aliases = entry.get("default_key_sizes", [])
        else:
            aliases = []

        attack_alg = assessment.get("attack_algorithm", "")
        attack_family = map_attack_algorithm_to_family(attack_alg)
        q_class = assessment.get("quantum_status", "UNKNOWN")

        # Resolve explicit calibration data if configured via parameter override or production provider
        va = None
        sp = None
        calib_status = "UNCONFIGURED"
        calib_version = "SENTRIQ QARS Prototype Heuristic Calibration v1"
        calib_source = "SENTRIQ_PROTOTYPE_HEURISTIC"
        calib_methodology = ""
        confidence = "INSUFFICIENT_EVIDENCE"

        if calibration_data and isinstance(calibration_data, dict):
            # Lookup by canonical name or raw name from custom dictionary fixture
            calib = calibration_data.get(canonical_name) or calibration_data.get(raw_name.upper())
            if calib and isinstance(calib, dict):
                va = calib.get("vulnerability_factor") or calib.get("Va")
                sp = calib.get("security_strength_factor") or calib.get("Sp")
                if va is not None and sp is not None:
                    va = max(0.0, min(1.0, float(va)))
                    sp = max(0.0, min(1.0, float(sp)))
                    calib_status = "CONFIGURED"
                    confidence = "PROVISIONAL"
                    calib_methodology = "Explicit custom calibration dictionary fixture applied."
        else:
            # Query versioned production calibration provider
            provider = get_default_calibration_provider()
            rec = provider.resolve_calibration(canonical_name, parameter=key_size)
            calib_status = rec.calibration_status
            calib_version = rec.calibration_version
            calib_source = rec.source
            calib_methodology = rec.methodology

            if rec.attack_family and rec.attack_family != "UNKNOWN":
                attack_family = rec.attack_family

            if calib_status == "CONFIGURED" and rec.vulnerability_factor is not None and rec.security_strength_factor is not None:
                va = rec.vulnerability_factor
                sp = rec.security_strength_factor
                confidence = rec.confidence
            else:
                va = None
                sp = None
                calib_status = "UNCONFIGURED"
                confidence = "INSUFFICIENT_EVIDENCE"

        return QuantumAlgorithmProfile(
            canonical_name=canonical_name,
            aliases=[str(a) for a in aliases],
            attack_family=attack_family,
            quantum_vulnerability_class=q_class,
            vulnerability_factor=va,
            security_strength_factor=sp,
            security_objectives=[],
            calibration_status=calib_status,
            source="QARS_KNOWLEDGE_BASE",
            confidence=confidence,
            calibration_version=calib_version,
            calibration_source=calib_source,
            calibration_methodology=calib_methodology,
            calibration_confidence=confidence
        )
