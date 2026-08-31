from typing import List, Dict, Any
from app.models.enums import CryptoPurpose, StandardStatus

def get_pqc_recommendations(purpose: CryptoPurpose, legacy_algorithm: str) -> List[Dict[str, Any]]:
    recommendations = []

    if purpose in [CryptoPurpose.KEY_ESTABLISHMENT, CryptoPurpose.ENCRYPTION]:
        recommendations.append({
            "target_pqc_candidate": "ML-KEM (FIPS 203)",
            "standard_status": StandardStatus.FINAL_STANDARD,
            "rationale": f"Primary NIST-standardized PQC replacement for key establishment / encryption currently using {legacy_algorithm}.",
            "compatibility_notes": "Requires protocol adjustment for KEM encapsulation interface instead of direct RSA key transport.",
            "performance_notes": "Slight increase in network payload size (~1KB public key). Excellent CPU efficiency.",
            "migration_complexity": "MEDIUM",
            "confidence": 0.95
        })

    elif purpose in [CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION]:
        recommendations.append({
            "target_pqc_candidate": "ML-DSA (FIPS 204)",
            "standard_status": StandardStatus.FINAL_STANDARD,
            "rationale": f"Primary NIST lattice-based signature replacement for {legacy_algorithm}.",
            "compatibility_notes": "Requires buffer updates for signature storage (~2.4KB - 4.6KB).",
            "performance_notes": "Very fast verification speed. Suitable for API tokens and TLS handshake signatures.",
            "migration_complexity": "MEDIUM",
            "confidence": 0.95
        })
        recommendations.append({
            "target_pqc_candidate": "SLH-DSA (FIPS 205)",
            "standard_status": StandardStatus.FINAL_STANDARD,
            "rationale": f"Conservative hash-based signature replacement for high-security, long-term offline signing using {legacy_algorithm}.",
            "compatibility_notes": "Large signature size (7.8KB - 49KB). Recommended for firmware signing or root CA certificates.",
            "performance_notes": "Higher computational overhead during signing; extremely small public key.",
            "migration_complexity": "HIGH",
            "confidence": 0.85
        })

    elif purpose == CryptoPurpose.HASHING:
        recommendations.append({
            "target_pqc_candidate": "SHA-3 / SHA-256+",
            "standard_status": StandardStatus.FINAL_STANDARD,
            "rationale": "Symmetric hash algorithms are inherently resistant to quantum attack; ensure minimum 256-bit output.",
            "compatibility_notes": "Drop-in replacement for legacy hashes like MD5 or SHA-1.",
            "performance_notes": "Standard CPU performance.",
            "migration_complexity": "LOW",
            "confidence": 0.90
        })

    else:
        recommendations.append({
            "target_pqc_candidate": "No standardized candidate found",
            "standard_status": StandardStatus.RESEARCH_NON_STANDARD,
            "rationale": f"The cryptographic purpose '{purpose}' could not be matched to a finalized NIST PQC standard.",
            "compatibility_notes": "Manual cryptography review required.",
            "performance_notes": "N/A",
            "migration_complexity": "HIGH",
            "confidence": 0.50
        })

    return recommendations
