from typing import Dict, Any, List, Optional
from app.models.enums import (
    CryptoPurpose, QuantumSafety, RiskLevel,
    StandardStatus, RecommendationCategory
)

class RecommendationEngine:
    """
    Deterministic PQC Recommendation Engine for Prompt 4.
    Purpose-first, risk-aware, threat-aware candidate selection.
    """
    def evaluate_recommendations(self, asset: Any) -> List[Dict[str, Any]]:
        detector_names = [e.detector_name for e in (getattr(asset, "evidence_items", []) or [])]
        rec = self.generate_recommendation(
            algorithm_name=getattr(asset, "algorithm_name", ""),
            purpose=getattr(asset, "purpose", CryptoPurpose.UNKNOWN),
            quantum_safety=getattr(asset, "quantum_safety", QuantumSafety.UNKNOWN),
            risk_level="LOW",
            risk_score=0.0,
            detector_names=detector_names
        )
        rec["asset_id"] = getattr(asset, "id", None)
        rec["asset_name"] = getattr(asset, "name", None)
        return [rec]

    def generate_recommendation(
        self,
        algorithm_name: str,
        purpose: CryptoPurpose,
        quantum_safety: QuantumSafety,
        risk_level: str = "LOW",
        risk_score: float = 0.0,
        threat_scenarios: Optional[List[Dict[str, Any]]] = None,
        migration_complexity: str = "MEDIUM",
        detector_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:

        alg_upper = (algorithm_name or "").strip().upper()
        threat_types = [t.get("scenario_type") for t in (threat_scenarios or [])]

        # 1. Determine Category, Candidates & Trade-offs based on Purpose & Algorithm
        category, primary_cand, alt_cand, std_status, tradeoffs, base_rationale = self._select_candidates(
            alg_upper, purpose, quantum_safety
        )

        # 2. Map Priority from Risk Level
        r_level_str = (risk_level or "LOW").upper()
        if r_level_str == "CRITICAL" or risk_score >= 75.0:
            priority = "CRITICAL"
        elif r_level_str in ["HIGH"] or risk_score >= 50.0:
            priority = "HIGH"
        elif r_level_str in ["MODERATE", "MEDIUM"] or risk_score >= 25.0:
            priority = "MODERATE"
        else:
            priority = "LOW"

        # 3. Determine Migration Notes from Migration Complexity
        comp_str = (migration_complexity or "MEDIUM").upper()
        if comp_str == "HIGH":
            migration_notes = "Phased migration recommended with extensive compatibility testing and human review due to complex dependencies/native binaries."
        elif comp_str == "MEDIUM":
            migration_notes = "Standard PQC migration recommended with automated testing and dependency updates."
        elif comp_str == "LOW":
            migration_notes = "Straightforward PQC transition via direct code or config update."
        else:
            migration_notes = "Cryptographic complexity assessment required prior to committing migration resources."

        # 4. Calculate Recommendation Confidence (independent of risk score)
        confidence = self._calculate_confidence(alg_upper, purpose, detector_names or [])

        # 5. Enrich Rationale with Threat & Risk Context
        rationale_lines = [base_rationale]

        if "HARVEST_NOW_DECRYPT_LATER" in threat_types:
            rationale_lines.append(
                "Urgent key establishment migration required due to Harvest-Now, Decrypt-Later (HNDL) exposure protecting long-lived sensitive data."
            )
        if "QUANTUM_SIGNATURE_FORGERY" in threat_types:
            rationale_lines.append(
                "Signature migration prioritized to prevent quantum private key derivation and digital signature forgery."
            )
        if "LONG_LIVED_DATA_EXPOSURE" in threat_types:
            rationale_lines.append(
                "Data protection lifetime extends beyond quantum threat horizon; transition to PQC or hybrid deployment is recommended."
            )

        if priority == "CRITICAL":
            rationale_lines.append("Assessed at CRITICAL risk. Immediate migration planning and pilot prototyping advised.")
        elif priority == "HIGH":
            rationale_lines.append("Assessed at HIGH risk. Prioritize PQC migration planning in upcoming engineering cycles.")
        elif priority == "LOW":
            rationale_lines.append("Assessed at LOW risk. Plan transition as part of ongoing crypto agility maintenance.")

        full_rationale = " ".join(rationale_lines)

        # Derive transformation pattern
        if category == RecommendationCategory.PQC_REPLACEMENT:
            if "ML-DSA" in primary_cand or purpose in [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION]:
                transformation_pattern = "RSA_TO_ML_DSA" if "RSA" in alg_upper else "ECDSA_TO_ML_DSA"
            elif "ML-KEM" in primary_cand or purpose == CryptoPurpose.KEY_ESTABLISHMENT:
                transformation_pattern = "ECDH_TO_ML_KEM_HYBRID"
            else:
                transformation_pattern = "RSA_TO_ML_DSA"
        elif category in [RecommendationCategory.RETAIN_SYMMETRIC_CRYPTO, RecommendationCategory.RETAIN_HASH, RecommendationCategory.RETAIN_MAC, RecommendationCategory.RETAIN_PASSWORD_DERIVATION]:
            transformation_pattern = "AES_256_GCM_RETENTION" if purpose == CryptoPurpose.ENCRYPTION else "RETAIN_EXISTING"
        else:
            transformation_pattern = "MANUAL_REVIEW"

        return {
            "target_pqc_candidate": primary_cand,
            "recommended_algorithm": primary_cand,
            "alternative_algorithm": alt_cand,
            "transformation_pattern": transformation_pattern,
            "category": category,
            "priority": priority,
            "standard_status": std_status,
            "rationale": full_rationale,
            "compatibility_notes": tradeoffs.get("compatibility_notes"),
            "performance_notes": tradeoffs.get("performance_notes"),
            "tradeoffs": tradeoffs,
            "threat_scenarios": threat_scenarios or [],
            "migration_notes": migration_notes,
            "migration_complexity": comp_str,
            "confidence": confidence,
            "kb_version": "2026.3.0-NIST-PQC"
        }

    def _select_candidates(
        self,
        alg_upper: str,
        purpose: CryptoPurpose,
        quantum_safety: QuantumSafety
    ):
        # 1. MAC (Check MAC before HASHING since HMAC contains SHA)
        if purpose == CryptoPurpose.MAC or "HMAC" in alg_upper:
            tradeoffs = {
                "algorithm": "RETAIN_MAC",
                "purpose": "MAC",
                "security_margin": "HMAC relies on symmetric hashing and is inherently quantum-resistant.",
                "compatibility_notes": "Drop-in symmetric message authentication.",
                "performance_notes": "Fast symmetric authentication."
            }
            return (
                RecommendationCategory.RETAIN_MAC,
                "RETAIN_EXISTING",
                "HMAC-SHA256+",
                StandardStatus.FINAL_STANDARD,
                tradeoffs,
                f"Message Authentication Code '{alg_upper}' uses symmetric hashing and does not require a PQC replacement."
            )

        # 2. HASHING
        if purpose == CryptoPurpose.HASHING or any(k in alg_upper for k in ["SHA", "BLAKE", "RIPEMD", "MD5"]):
            tradeoffs = {
                "algorithm": "RETAIN_HASH",
                "purpose": "HASHING",
                "security_margin": "Symmetric hash functions (SHA-256, SHA-384, SHA-512, SHA-3) retain sufficient quantum security.",
                "compatibility_notes": "Ensure output size is at least 256 bits.",
                "performance_notes": "High performance standard CPU hashing."
            }
            return (
                RecommendationCategory.RETAIN_HASH,
                "RETAIN_EXISTING",
                "SHA-3 / SHA-256+",
                StandardStatus.FINAL_STANDARD,
                tradeoffs,
                f"Cryptographic hash function '{alg_upper}' is inherently quantum-resistant. Retain existing hash algorithm with 256+ bit output."
            )

        # 3. PASSWORD DERIVATION
        if purpose == CryptoPurpose.PASSWORD_DERIVATION or any(k in alg_upper for k in ["PBKDF2", "ARGON2", "BCRYPT", "SCRYPT"]):
            tradeoffs = {
                "algorithm": "RETAIN_PASSWORD_DERIVATION",
                "purpose": "PASSWORD_DERIVATION",
                "security_margin": "Password key derivation functions do not use public-key cryptography and are not broken by Shor's algorithm.",
                "compatibility_notes": "Retain iterative/memory-hard password hashing.",
                "performance_notes": "Configured memory and work factors control brute-force resistance."
            }
            return (
                RecommendationCategory.RETAIN_PASSWORD_DERIVATION,
                "RETAIN_EXISTING",
                "ARGON2ID",
                StandardStatus.FINAL_STANDARD,
                tradeoffs,
                f"Password derivation function '{alg_upper}' is not vulnerable to public-key quantum attacks. Retain existing KDF."
            )

        # 4. SYMMETRIC ENCRYPTION (AES, ChaCha20, DES)
        if purpose == CryptoPurpose.ENCRYPTION or any(k in alg_upper for k in ["AES", "CHACHA", "SALSA", "DES"]):
            tradeoffs = {
                "algorithm": "RETAIN_SYMMETRIC_CRYPTO",
                "purpose": "ENCRYPTION",
                "security_margin": "AES/ChaCha20 symmetric encryption retains 128+ bits of security against Grover's algorithm.",
                "compatibility_notes": "No direct PQC algorithm replaces AES. Retain symmetric encryption with 256-bit keys (e.g., AES-256-GCM).",
                "performance_notes": "Excellent hardware-accelerated CPU performance (AES-NI).",
                "action": "Focus PQC migration on protecting key establishment/wrapping used to establish symmetric keys."
            }
            return (
                RecommendationCategory.RETAIN_SYMMETRIC_CRYPTO,
                "RETAIN_EXISTING",
                "AES-256-GCM",
                StandardStatus.FINAL_STANDARD,
                tradeoffs,
                f"Symmetric encryption algorithm '{alg_upper}' is not broken by Shor's algorithm. Retain symmetric encryption (upgrade to AES-256-GCM) and protect key establishment with PQC."
            )

        # 5. KEY ESTABLISHMENT (ECDH, DH, X25519, X448, RSA Key Exchange)
        if purpose == CryptoPurpose.KEY_ESTABLISHMENT or any(k in alg_upper for k in ["ECDH", "X25519", "X448", "DH", "DIFFIE"]) or (any(k in alg_upper for k in ["RSA"]) and purpose == CryptoPurpose.KEY_ESTABLISHMENT):
            tradeoffs = {
                "algorithm": "ML-KEM (FIPS 203)",
                "purpose": "KEY_ESTABLISHMENT",
                "artifact_sizes": "Public key: 800-1568 bytes; Ciphertext: 768-1568 bytes.",
                "compatibility_notes": "Requires protocol adjustment for KEM encapsulation interface instead of direct key exchange/transport.",
                "performance_notes": "Fast encapsulation and decapsulation efficiency. Benchmark network payload impact.",
                "alternative_approach": "Hybrid mode combining classical ECDH + ML-KEM preserves compatibility during migration."
            }
            return (
                RecommendationCategory.PQC_REPLACEMENT,
                "ML-KEM (FIPS 203)",
                "HYBRID (ECDH + ML-KEM)",
                StandardStatus.FINAL_STANDARD,
                tradeoffs,
                f"ML-KEM (FIPS 203) is the primary NIST-standardized PQC replacement for key establishment using '{alg_upper}'."
            )

        # 6. DIGITAL SIGNATURE (RSA, ECDSA, DSA, Ed25519, Ed448)
        if purpose in [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION] or any(k in alg_upper for k in ["ECDSA", "ED25519", "ED448", "DSA", "RSA"]):
            tradeoffs = {
                "algorithm": "ML-DSA (FIPS 204)",
                "purpose": "DIGITAL_SIGNATURE",
                "artifact_sizes": "Public key: 1.3KB-2.6KB; Signature: 2.4KB-4.6KB.",
                "compatibility_notes": "Requires buffer updates for signature storage (~2.4KB-4.6KB).",
                "performance_notes": "High verification performance. Suitable for TLS handshakes and token signing.",
                "alternative_approach": "SLH-DSA (FIPS 205) is a conservative hash-based signature alternative for long-term root CA or firmware signing."
            }
            return (
                RecommendationCategory.PQC_REPLACEMENT,
                "ML-DSA (FIPS 204)",
                "SLH-DSA (FIPS 205)",
                StandardStatus.FINAL_STANDARD,
                tradeoffs,
                f"ML-DSA (FIPS 204) is the primary NIST lattice-based signature replacement for '{alg_upper}'."
            )

        # 7. UNKNOWN / CUSTOM / HSM / VENDOR
        tradeoffs = {
            "algorithm": "MANUAL_REVIEW",
            "purpose": "UNKNOWN",
            "compatibility_notes": "Cryptographic purpose or algorithm classification is unknown. Manual cryptography audit required.",
            "performance_notes": "N/A"
        }
        return (
            RecommendationCategory.MANUAL_REVIEW,
            "MANUAL_REVIEW_REQUIRED",
            "N/A",
            StandardStatus.RESEARCH_NON_STANDARD,
            tradeoffs,
            f"The cryptographic asset '{alg_upper}' could not be deterministically mapped to a standardized PQC candidate. Manual review required."
        )


    def _calculate_confidence(
        self,
        alg_upper: str,
        purpose: CryptoPurpose,
        detector_names: List[str]
    ) -> float:
        if not alg_upper or alg_upper == "UNKNOWN" or purpose == CryptoPurpose.UNKNOWN:
            return 0.40

        detectors = [d.lower() for d in (detector_names or [])]
        base_conf = 0.85

        for d in detectors:
            if "sourcescanner" in d or "certificatescanner" in d:
                base_conf = max(base_conf, 0.95)
            elif "dependencyscanner" in d:
                base_conf = max(base_conf, 0.85)
            elif "binaryscanner" in d or "containerscanner" in d:
                base_conf = min(base_conf, 0.65)

        return round(base_conf, 2)
