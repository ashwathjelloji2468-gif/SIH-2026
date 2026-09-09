import re
from typing import Dict, Any, Optional
from app.models.enums import CryptoPurpose, StandardStatus

CRYPTO_CATALOG: Dict[str, Dict[str, Any]] = {
    "RSA": {
        "family": "Asymmetric",
        "quantum_vulnerable": True,
        "purposes": [CryptoPurpose.SIGNATURE, CryptoPurpose.KEY_ESTABLISHMENT, CryptoPurpose.ENCRYPTION],
        "status": StandardStatus.FINAL_STANDARD,
        "default_key_sizes": [2048, 3072, 4096],
        "quantum_assessment": {
            "quantum_status": "CRITICAL",
            "attack_algorithm": "Shor's Algorithm",
            "quantum_effect": "Polynomial-time integer factorization cryptanalysis via Shor's algorithm completely breaks RSA security.",
            "rationale": "Shor's algorithm solves integer factorization in O(n^3) quantum operations, invalidating prime-factorization based security.",
            "recommended_action": "Migrate to NIST PQC standards (ML-KEM for key establishment/encryption, ML-DSA or SLH-DSA for digital signatures).",
            "confidence": "HIGH"
        }
    },
    "ECDSA": {
        "family": "Asymmetric",
        "quantum_vulnerable": True,
        "purposes": [CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION],
        "status": StandardStatus.FINAL_STANDARD,
        "default_key_sizes": [256, 384, 521],
        "quantum_assessment": {
            "quantum_status": "CRITICAL",
            "attack_algorithm": "Shor's Algorithm",
            "quantum_effect": "Polynomial-time elliptic curve discrete logarithm cryptanalysis via Shor's algorithm completely breaks ECDSA signatures.",
            "rationale": "Shor's algorithm solves elliptic curve discrete logarithm problems in polynomial time.",
            "recommended_action": "Migrate to NIST PQC digital signature standards (ML-DSA or SLH-DSA).",
            "confidence": "HIGH"
        }
    },
    "ECDH": {
        "family": "Asymmetric",
        "quantum_vulnerable": True,
        "purposes": [CryptoPurpose.KEY_ESTABLISHMENT],
        "status": StandardStatus.FINAL_STANDARD,
        "default_key_sizes": [256, 384, 521],
        "quantum_assessment": {
            "quantum_status": "CRITICAL",
            "attack_algorithm": "Shor's Algorithm",
            "quantum_effect": "Polynomial-time discrete logarithm cryptanalysis allows quantum adversary to compute shared secret.",
            "rationale": "Shor's algorithm breaks ECDH key exchange by computing private keys from public keys in polynomial time.",
            "recommended_action": "Migrate to ML-KEM (FIPS 203) or hybrid ECDH + ML-KEM key exchange.",
            "confidence": "HIGH"
        }
    },
    "AES": {
        "family": "Symmetric",
        "quantum_vulnerable": False,  # AES-256 is quantum resistant
        "purposes": [CryptoPurpose.ENCRYPTION],
        "status": StandardStatus.FINAL_STANDARD,
        "default_key_sizes": [128, 192, 256],
        "quantum_assessment": {
            "quantum_status": "PARAMETER_DEPENDENT",
            "attack_algorithm": "Grover's Algorithm",
            "quantum_effect": "Grover's quadratic search speedup halves effective key security (e.g. 128-bit key -> ~64-bit security margin).",
            "rationale": "Grover's algorithm reduces symmetric brute force search complexity from N to sqrt(N). AES-256 maintains 128-bit quantum security, while AES-128 drops to ~64 bits.",
            "recommended_action": "Enforce AES-256 to ensure a 128-bit post-quantum security margin.",
            "confidence": "HIGH"
        }
    },
    "SHA-256": {
        "family": "Hash",
        "quantum_vulnerable": False,
        "purposes": [CryptoPurpose.HASHING],
        "status": StandardStatus.FINAL_STANDARD,
        "default_key_sizes": [],
        "quantum_assessment": {
            "quantum_status": "LOW",
            "attack_algorithm": "Grover's Algorithm (Preimage) / BHT Algorithm (Collision)",
            "quantum_effect": "Preimage resistance reduced to 128 bits; collision resistance reduced to ~85 bits under quantum BHT algorithm.",
            "rationale": "256-bit output size retains a 128-bit quantum preimage security margin under Grover's algorithm.",
            "recommended_action": "Retain algorithm; enforce minimum output size >= 256 bits.",
            "confidence": "HIGH"
        }
    },
    "MD5": {
        "family": "Hash",
        "quantum_vulnerable": True,  # Broken classically and quantum
        "purposes": [CryptoPurpose.HASHING],
        "status": StandardStatus.RESEARCH_NON_STANDARD,
        "default_key_sizes": [],
        "quantum_assessment": {
            "quantum_status": "CRITICAL",
            "attack_algorithm": "Grover's Algorithm / BHT Algorithm",
            "quantum_effect": "Classically collision-broken; quantum Grover search reduces 128-bit preimage resistance to ~64 bits.",
            "rationale": "MD5 suffers from complete classical collision vulnerabilities and severe quantum security reduction.",
            "recommended_action": "Replace with SHA-256, SHA-512, or SHA-3.",
            "confidence": "HIGH"
        }
    },
    "DES": {
        "family": "Symmetric",
        "quantum_vulnerable": True,
        "purposes": [CryptoPurpose.ENCRYPTION],
        "status": StandardStatus.RESEARCH_NON_STANDARD,
        "default_key_sizes": [56],
        "quantum_assessment": {
            "quantum_status": "CRITICAL",
            "attack_algorithm": "Grover's Algorithm",
            "quantum_effect": "56-bit key reduced to 28-bit quantum security margin; trivially broken classically and quantumly.",
            "rationale": "Small key size is completely insecure classically and further reduced under Grover's search.",
            "recommended_action": "Replace immediately with AES-256.",
            "confidence": "HIGH"
        }
    }
}


def evaluate_quantum_assessment(
    algorithm_name: str,
    key_size: Optional[int] = None,
    purpose: Optional[CryptoPurpose] = None
) -> Dict[str, Any]:
    """Parameter-aware quantum vulnerability assessment engine.

    Evaluates cryptographic algorithm, parameter (key size), and purpose to produce
    an explainable, fine-grained quantum risk analysis.
    """
    if not algorithm_name or not str(algorithm_name).strip():
        return {
            "algorithm": "UNKNOWN",
            "parameter": "N/A",
            "quantum_status": "UNKNOWN",
            "attack_algorithm": "None",
            "quantum_effect": "Quantum vulnerability assessment could not be determined for missing algorithm name.",
            "rationale": "Algorithm name was omitted or empty.",
            "recommended_action": "MANUAL_CRYPTOGRAPHIC_REVIEW",
            "confidence": "INSUFFICIENT_EVIDENCE"
        }

    raw_name = str(algorithm_name).strip()
    alg_upper = raw_name.upper()

    # Extract key_size from name if not explicitly provided
    effective_key_size = key_size
    if effective_key_size is None:
        match = re.search(r"(\d+)", alg_upper)
        if match:
            extracted_num = int(match.group(1))
            # Distinguish output bits for hash functions vs key sizes for ciphers/asymmetric
            if not any(h in alg_upper for h in ["SHA", "MD5", "BLAKE", "RIPEMD"]):
                effective_key_size = extracted_num

    param_str = f"key_size={effective_key_size}" if effective_key_size else "N/A"

    # 1. Asymmetric Cryptography (RSA, ECDSA, ECDH, Ed25519, X25519, DSA, DH, ECC)
    if any(p in alg_upper for p in ["RSA", "ECDSA", "ECDH", "ED25519", "X25519", "DSA", "DH", "DIFFIE", "EC", "ECC"]):
        return {
            "algorithm": raw_name,
            "parameter": param_str,
            "quantum_status": "CRITICAL",
            "attack_algorithm": "Shor's Algorithm",
            "quantum_effect": "Polynomial-time integer factorization or discrete logarithm cryptanalysis via Shor's algorithm completely invalidates key security.",
            "rationale": f"Quantum computers equipped with sufficient logical qubits running Shor's algorithm solve discrete logarithms and prime factorization in O(n^3) polynomial time. {raw_name} security is completely broken regardless of key length.",
            "recommended_action": "Migrate to NIST Post-Quantum Cryptography standards (ML-KEM for key establishment/encryption, ML-DSA or SLH-DSA for digital signatures).",
            "confidence": "HIGH"
        }

    # 2. Symmetric Cryptography (AES, ChaCha20, DES, 3DES)
    if "AES" in alg_upper:
        if effective_key_size and effective_key_size < 192:
            return {
                "algorithm": f"AES-{effective_key_size}" if f"AES-{effective_key_size}" not in raw_name else raw_name,
                "parameter": param_str,
                "quantum_status": "PARAMETER_DEPENDENT",
                "attack_algorithm": "Grover's Algorithm",
                "quantum_effect": "Grover's quadratic search speedup reduces effective key security from 128 bits to ~64 bits.",
                "rationale": "Grover's algorithm reduces brute-force search complexity from N to sqrt(N). For 128-bit symmetric keys, quantum search complexity drops to 2^64 operations, falling below acceptable long-term security thresholds.",
                "recommended_action": "Upgrade key size to AES-256 or adopt ChaCha20 with 256-bit keys to preserve a 128-bit post-quantum security margin.",
                "confidence": "HIGH"
            }
        elif effective_key_size == 192:
            return {
                "algorithm": "AES-192",
                "parameter": param_str,
                "quantum_status": "MODERATE",
                "attack_algorithm": "Grover's Algorithm",
                "quantum_effect": "Reduces effective key security from 192 bits to ~96 bits.",
                "rationale": "Grover's search reduces 192-bit search complexity to ~2^96 quantum operations.",
                "recommended_action": "Upgrade to AES-256 for optimal post-quantum security margin.",
                "confidence": "HIGH"
            }
        else:
            # AES-256 or general AES
            return {
                "algorithm": raw_name if "256" in raw_name else ("AES-256" if effective_key_size == 256 else raw_name),
                "parameter": param_str,
                "quantum_status": "LOW",
                "attack_algorithm": "Grover's Algorithm",
                "quantum_effect": "Security margin reduced to ~128 bits, retaining strong post-quantum protection.",
                "rationale": "Grover's search reduces 256-bit key search complexity to 2^128 operations, which remains computationally infeasible and compliant with NIST PQC guidelines.",
                "recommended_action": "Retain algorithm; monitor implementation security.",
                "confidence": "HIGH"
            }

    if any(d in alg_upper for d in ["DES", "3DES", "TRIPLEDES"]):
        return {
            "algorithm": raw_name,
            "parameter": param_str,
            "quantum_status": "CRITICAL",
            "attack_algorithm": "Grover's Algorithm",
            "quantum_effect": "Effective key security reduced to ~28-56 bits; trivially broken both classically and quantumly.",
            "rationale": "DES/3DES rely on small key sizes that are insecure classically and further reduced under Grover's search.",
            "recommended_action": "Replace immediately with AES-256.",
            "confidence": "HIGH"
        }

    if "CHACHA" in alg_upper:
        return {
            "algorithm": raw_name,
            "parameter": param_str,
            "quantum_status": "LOW",
            "attack_algorithm": "Grover's Algorithm",
            "quantum_effect": "Retains 128 bits of security against Grover's algorithm with 256-bit key.",
            "rationale": "ChaCha20 utilizes a 256-bit key size yielding a 128-bit quantum security margin.",
            "recommended_action": "Retain algorithm; maintain 256-bit key size.",
            "confidence": "HIGH"
        }

    # 3. Hash Functions
    if any(m in alg_upper for m in ["MD5", "SHA1", "SHA-1"]):
        return {
            "algorithm": raw_name,
            "parameter": param_str,
            "quantum_status": "CRITICAL",
            "attack_algorithm": "Grover's Algorithm / BHT Algorithm",
            "quantum_effect": "Classically collision-broken; quantum preimage resistance reduced to ~64 bits.",
            "rationale": f"{raw_name} suffers from complete classical collision vulnerabilities, compounded by Grover preimage search acceleration.",
            "recommended_action": "Replace with SHA-256, SHA-512, or SHA-3.",
            "confidence": "HIGH"
        }

    if any(h in alg_upper for h in ["SHA-256", "SHA256", "SHA-384", "SHA384", "SHA-512", "SHA512", "SHA-3", "SHA3", "BLAKE2", "ARGON2", "BCRYPT"]):
        return {
            "algorithm": raw_name,
            "parameter": param_str,
            "quantum_status": "LOW",
            "attack_algorithm": "Grover's Algorithm (Preimage) / BHT Algorithm (Collision)",
            "quantum_effect": "Preimage resistance reduced to n/2 bits; collision resistance reduced to n/3 bits (or 128-bit security margin for SHA-256).",
            "rationale": f"{raw_name} hash function with output length >= 256 bits provides at least 128 bits of quantum preimage security under Grover's search (~2^128 operations) and acceptable BHT collision bounds.",
            "recommended_action": "Retain algorithm; enforce minimum output size >= 256 bits.",
            "confidence": "HIGH"
        }

    # 4. NIST PQC Candidates
    if any(pqc in alg_upper for pqc in ["ML-KEM", "ML-DSA", "SLH-DSA", "CRYSTALS", "FALCON", "SPHINCS", "PQC"]):
        return {
            "algorithm": raw_name,
            "parameter": param_str,
            "quantum_status": "LOW",
            "attack_algorithm": "None",
            "quantum_effect": "NIST-standardized post-quantum algorithm designed specifically to resist quantum cryptanalysis.",
            "rationale": f"{raw_name} is based on hard lattice or hash-based cryptographic problems that are resistant to both Shor's and Grover's algorithms.",
            "recommended_action": "Retain algorithm; verify parameter set alignment with FIPS standards.",
            "confidence": "HIGH"
        }

    # 5. Catalog Fallback
    catalog_entry = CRYPTO_CATALOG.get(alg_upper)
    if catalog_entry:
        is_vuln = catalog_entry.get("quantum_vulnerable", False)
        qa = catalog_entry.get("quantum_assessment", {})
        return {
            "algorithm": raw_name,
            "parameter": param_str,
            "quantum_status": qa.get("quantum_status", "HIGH" if is_vuln else "LOW"),
            "attack_algorithm": qa.get("attack_algorithm", "Shor's Algorithm" if is_vuln else "Grover's Algorithm"),
            "quantum_effect": qa.get("quantum_effect", "Cataloged cryptographic primitive."),
            "rationale": qa.get("rationale", f"Catalog entry for {raw_name} evaluates quantum vulnerability as {is_vuln}."),
            "recommended_action": qa.get("recommended_action", "Migrate to quantum-safe alternative." if is_vuln else "Retain algorithm."),
            "confidence": qa.get("confidence", "MEDIUM")
        }

    # 6. Unknown / Unclassified Algorithms
    return {
        "algorithm": raw_name,
        "parameter": param_str,
        "quantum_status": "UNKNOWN",
        "attack_algorithm": "None",
        "quantum_effect": "Quantum vulnerability assessment could not be determined for unrecognized primitive.",
        "rationale": f"Algorithm '{raw_name}' is not cataloged in the SENTRIQ post-quantum knowledge base.",
        "recommended_action": "MANUAL_CRYPTOGRAPHIC_REVIEW",
        "confidence": "INSUFFICIENT_EVIDENCE"
    }

