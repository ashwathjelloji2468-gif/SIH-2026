from typing import List, Dict, Any
from app.models.enums import ThreatScenarioType, QuantumSafety, CryptoPurpose

def evaluate_threat_scenarios(
    algorithm_name: str,
    quantum_safety: QuantumSafety,
    purpose: CryptoPurpose,
    data_sensitivity_label: str,
    data_lifetime_years: float,
    mosca_status: str,
    evidence_excerpts: List[str] = None
) -> List[Dict[str, Any]]:
    scenarios = []
    evidence_refs = evidence_excerpts or []

    # 1. Harvest Now Decrypt Later (HNDL)
    is_key_est_or_enc = (purpose in [CryptoPurpose.KEY_ESTABLISHMENT, CryptoPurpose.ENCRYPTION, CryptoPurpose.UNKNOWN])
    is_vulnerable = (quantum_safety == QuantumSafety.QUANTUM_VULNERABLE)
    is_sensitive = data_sensitivity_label.upper() in ["CONFIDENTIAL", "RESTRICTED", "CRITICAL", "UNKNOWN"]

    if is_vulnerable and is_key_est_or_enc and (is_sensitive or data_lifetime_years >= 3):
        scenarios.append({
            "scenario_type": ThreatScenarioType.HARVEST_NOW_DECRYPT_LATER,
            "name": "Harvest-Now, Decrypt-Later (HNDL)",
            "severity": "CRITICAL" if data_sensitivity_label.upper() in ["RESTRICTED", "CRITICAL"] else "HIGH",
            "urgency": "CRITICAL" if mosca_status in ["DEADLINE_RISK", "MIGRATION_REQUIRED"] else "HIGH",
            "description": "Adversaries store encrypted traffic/key-exchanges now to decrypt when quantum capability emerges.",
            "rationale": (
                f"Asset '{algorithm_name}' uses quantum-vulnerable key establishment/encryption. "
                f"Encrypted payload with sensitivity '{data_sensitivity_label}' and protection lifetime {data_lifetime_years}y is exposed to HNDL capture."
            ),
            "evidence": evidence_refs[:3]
        })

    # 2. Quantum Signature Forgery
    is_signature = (purpose in [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION])
    if is_vulnerable and is_signature:
        scenarios.append({
            "scenario_type": ThreatScenarioType.QUANTUM_SIGNATURE_FORGERY,
            "name": "Quantum Signature Forgery",
            "severity": "CRITICAL" if data_sensitivity_label.upper() in ["RESTRICTED", "CRITICAL"] else "HIGH",
            "urgency": "HIGH",
            "description": "Quantum computers running Shor's algorithm can derive private signing keys from public keys or certificates.",
            "rationale": (
                f"Asset '{algorithm_name}' is used for digital signatures/authentication. "
                f"A quantum computer can derive the private key to forge digital signatures and impersonate identities."
            ),
            "evidence": evidence_refs[:3]
        })

    # 3. Long-Lived Data Exposure
    if data_lifetime_years >= 5 and (is_vulnerable or quantum_safety == QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN) and mosca_status in ["DEADLINE_RISK", "MIGRATION_REQUIRED"]:
        scenarios.append({
            "scenario_type": ThreatScenarioType.LONG_LIVED_DATA_EXPOSURE,
            "name": "Long-Lived Data Exposure",
            "severity": "HIGH",
            "urgency": "HIGH" if mosca_status == "DEADLINE_RISK" else "MODERATE",
            "description": "Data requires protection beyond the estimated arrival of quantum threat capabilities.",
            "rationale": (
                f"Data protection lifetime ({data_lifetime_years}y) extends past the quantum threat horizon. "
                f"Mosca analysis status is '{mosca_status}'."
            ),
            "evidence": evidence_refs[:3]
        })

    return scenarios
