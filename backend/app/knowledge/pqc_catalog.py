from typing import Dict, Any, List, Optional
from app.models.enums import CryptoPurpose, StandardStatus

CATALOG_VERSION = "2026.3.0-NIST-PQC-AUTHORITATIVE"

PQC_CATALOG: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # KEY ENCAPSULATION MECHANISMS (KEM) - FIPS 203
    # -------------------------------------------------------------------------
    "ML-KEM-512": {
        "algorithm": "ML-KEM-512",
        "family": "ML-KEM",
        "standard_code": "FIPS 203",
        "primitive": "KEY_ESTABLISHMENT",
        "purposes": [CryptoPurpose.KEY_ESTABLISHMENT],
        "security_objectives": ["confidentiality", "key_establishment"],
        "security_level": 1,  # AES-128 equivalent (NIST FIPS 203 Table 1)
        "status": StandardStatus.FINAL_STANDARD,
        "pubkey_size_bytes": 800,  # Standard specification value (FIPS 203 Table 2)
        "ciphertext_size_bytes": 768,  # Standard specification value (FIPS 203 Table 2)
        "signature_size_bytes": None,
        "library_support": {
            "native_openssl": "OpenSSL 3.5+",
            "oqs_provider": "oqs-provider 0.6.0+",
            "liboqs": "liboqs 0.10.0+",
            "bouncycastle": "BouncyCastle 1.77+",
            "golang_crypto": "Go 1.24+"
        },
        "protocol_support": {
            "tls13": "TLS 1.3 (Draft/RFC)",
            "ssh": "SSHv2 (IETF Draft)",
            "ipsec": "IKEv2 (IETF Draft)",
            "x509": "N/A (KEM)"
        },
        "hybrid_support": True,
        "standard_provenance": "NIST FIPS 203 (Specification)",
        "measurement_provenance": "liboqs 0.10.0 / PQC Benchmark Dataset",
        "provenance": "NIST FIPS 203 (Specification) / liboqs Benchmarks",
        "measurement_status": "MEASURED",
        "performance_notes": "Fast CPU encapsulation (~0.01ms); measured lightweight key exchange."
    },
    "ML-KEM-768": {
        "algorithm": "ML-KEM-768",
        "family": "ML-KEM",
        "standard_code": "FIPS 203",
        "primitive": "KEY_ESTABLISHMENT",
        "purposes": [CryptoPurpose.KEY_ESTABLISHMENT],
        "security_objectives": ["confidentiality", "key_establishment"],
        "security_level": 3,  # AES-192 equivalent (NIST FIPS 203 Table 1)
        "status": StandardStatus.FINAL_STANDARD,
        "pubkey_size_bytes": 1184,  # Standard specification value (FIPS 203 Table 2)
        "ciphertext_size_bytes": 1088,  # Standard specification value (FIPS 203 Table 2)
        "signature_size_bytes": None,
        "library_support": {
            "native_openssl": "OpenSSL 3.5+",
            "oqs_provider": "oqs-provider 0.6.0+",
            "liboqs": "liboqs 0.10.0+",
            "bouncycastle": "BouncyCastle 1.77+",
            "golang_crypto": "Go 1.24+"
        },
        "protocol_support": {
            "tls13": "TLS 1.3 (Draft/RFC)",
            "ssh": "SSHv2 (IETF Draft)",
            "ipsec": "IKEv2 (IETF Draft)",
            "x509": "N/A (KEM)"
        },
        "hybrid_support": True,
        "standard_provenance": "NIST FIPS 203 (Specification)",
        "measurement_provenance": "liboqs 0.10.0 / PQC Benchmark Dataset",
        "provenance": "NIST FIPS 203 (Specification) / liboqs Benchmarks",
        "measurement_status": "MEASURED",
        "performance_notes": "NIST recommended primary KEM candidate. Measured balanced CPU latency."
    },
    "ML-KEM-1024": {
        "algorithm": "ML-KEM-1024",
        "family": "ML-KEM",
        "standard_code": "FIPS 203",
        "primitive": "KEY_ESTABLISHMENT",
        "purposes": [CryptoPurpose.KEY_ESTABLISHMENT],
        "security_objectives": ["confidentiality", "key_establishment"],
        "security_level": 5,  # AES-256 equivalent (NIST FIPS 203 Table 1)
        "status": StandardStatus.FINAL_STANDARD,
        "pubkey_size_bytes": 1568,  # Standard specification value (FIPS 203 Table 2)
        "ciphertext_size_bytes": 1568,  # Standard specification value (FIPS 203 Table 2)
        "signature_size_bytes": None,
        "library_support": {
            "native_openssl": "OpenSSL 3.5+",
            "oqs_provider": "oqs-provider 0.6.0+",
            "liboqs": "liboqs 0.10.0+",
            "bouncycastle": "BouncyCastle 1.77+",
            "golang_crypto": "Go 1.24+"
        },
        "protocol_support": {
            "tls13": "TLS 1.3 (Draft/RFC)",
            "ssh": "SSHv2 (IETF Draft)",
            "ipsec": "IKEv2 (IETF Draft)",
            "x509": "N/A (KEM)"
        },
        "hybrid_support": True,
        "standard_provenance": "NIST FIPS 203 (Specification)",
        "measurement_provenance": "liboqs 0.10.0 / PQC Benchmark Dataset",
        "provenance": "NIST FIPS 203 (Specification) / liboqs Benchmarks",
        "measurement_status": "MEASURED",
        "performance_notes": "Maximum security margin. Measured public key and ciphertext 1.5KB each."
    },

    # -------------------------------------------------------------------------
    # EXPLICIT HYBRID KEM CONFIGURATIONS
    # -------------------------------------------------------------------------
    "X25519_MLKEM768": {
        "algorithm": "X25519_MLKEM768",
        "family": "HYBRID_KEM",
        "standard_code": "IETF Draft / FIPS 203",
        "primitive": "KEY_ESTABLISHMENT",
        "purposes": [CryptoPurpose.KEY_ESTABLISHMENT],
        "security_objectives": ["confidentiality", "key_establishment"],
        "security_level": 3,
        "status": StandardStatus.FINAL_STANDARD,
        "pubkey_size_bytes": 1216,  # 32 (X25519) + 1184 (ML-KEM-768)
        "ciphertext_size_bytes": 1120,  # 32 + 1088
        "signature_size_bytes": None,
        "library_support": {
            "native_openssl": "OpenSSL 3.5+",
            "oqs_provider": "oqs-provider 0.6.0+",
            "liboqs": "liboqs 0.10.0+",
            "bouncycastle": "BouncyCastle 1.77+",
            "golang_crypto": "Go 1.24+"
        },
        "protocol_support": {
            "tls13": "TLS 1.3 (Codepoint 0x11EC)",
            "ssh": "SSHv2",
            "ipsec": "IKEv2",
            "x509": "N/A"
        },
        "hybrid_support": True,
        "standard_provenance": "IETF draft-ietf-tls-hybrid-design",
        "measurement_provenance": "OpenSSL 3.5 / oqs-provider Experiments",
        "provenance": "IETF draft-ietf-tls-hybrid-design / OpenSSL 3.5 Experiments",
        "measurement_status": "MEASURED",
        "performance_notes": "Combines classical X25519 ECDH resilience with post-quantum ML-KEM-768."
    },
    "SecP256r1_MLKEM768": {
        "algorithm": "SecP256r1_MLKEM768",
        "family": "HYBRID_KEM",
        "standard_code": "IETF Draft / FIPS 203",
        "primitive": "KEY_ESTABLISHMENT",
        "purposes": [CryptoPurpose.KEY_ESTABLISHMENT],
        "security_objectives": ["confidentiality", "key_establishment"],
        "security_level": 3,
        "status": StandardStatus.FINAL_STANDARD,
        "pubkey_size_bytes": 1249,  # 65 + 1184
        "ciphertext_size_bytes": 1153,  # 65 + 1088
        "signature_size_bytes": None,
        "library_support": {
            "native_openssl": "OpenSSL 3.5+",
            "oqs_provider": "oqs-provider 0.6.0+",
            "liboqs": "liboqs 0.10.0+",
            "bouncycastle": "BouncyCastle 1.77+",
            "golang_crypto": "Go 1.24+"
        },
        "protocol_support": {
            "tls13": "TLS 1.3 (Codepoint 0x11EB)",
            "ssh": "SSHv2",
            "ipsec": "IKEv2",
            "x509": "N/A"
        },
        "hybrid_support": True,
        "standard_provenance": "IETF draft-ietf-tls-hybrid-design",
        "measurement_provenance": "OpenSSL 3.5 / oqs-provider Experiments",
        "provenance": "IETF draft-ietf-tls-hybrid-design / OpenSSL 3.5 Experiments",
        "measurement_status": "MEASURED",
        "performance_notes": "FIPS 140-3 compliant classical secp256r1 ECDH paired with PQC ML-KEM-768."
    },

    # -------------------------------------------------------------------------
    # DIGITAL SIGNATURE ALGORITHMS (ML-DSA) - FIPS 204
    # -------------------------------------------------------------------------
    "ML-DSA-44": {
        "algorithm": "ML-DSA-44",
        "family": "ML-DSA",
        "standard_code": "FIPS 204",
        "primitive": "DIGITAL_SIGNATURE",
        "purposes": [CryptoPurpose.SIGNATURE, CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.AUTHENTICATION],
        "security_objectives": ["integrity", "authentication"],
        "security_level": 2,  # NIST FIPS 204 Table 1
        "status": StandardStatus.FINAL_STANDARD,
        "pubkey_size_bytes": 1312,  # Standard specification value (FIPS 204 Table 2)
        "ciphertext_size_bytes": None,
        "signature_size_bytes": 2420,  # Standard specification value (FIPS 204 Table 2)
        "library_support": {
            "native_openssl": "OpenSSL 3.5+",
            "oqs_provider": "oqs-provider 0.6.0+",
            "liboqs": "liboqs 0.10.0+",
            "bouncycastle": "BouncyCastle 1.77+",
            "golang_crypto": "Go 1.24+"
        },
        "protocol_support": {
            "tls13": "TLS 1.3 (Signatures)",
            "ssh": "SSHv2",
            "x509": "X.509 Certificates (RFC Draft)",
            "ipsec": "IKEv2"
        },
        "hybrid_support": True,
        "standard_provenance": "NIST FIPS 204 (Specification)",
        "measurement_provenance": "liboqs 0.10.0 / PQC Benchmark Dataset",
        "provenance": "NIST FIPS 204 (Specification) / liboqs Benchmarks",
        "measurement_status": "MEASURED",
        "performance_notes": "Fast verification speed; measured signature size ~2.4KB."
    },
    "ML-DSA-65": {
        "algorithm": "ML-DSA-65",
        "family": "ML-DSA",
        "standard_code": "FIPS 204",
        "primitive": "DIGITAL_SIGNATURE",
        "purposes": [CryptoPurpose.SIGNATURE, CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.AUTHENTICATION],
        "security_objectives": ["integrity", "authentication"],
        "security_level": 3,  # NIST FIPS 204 Table 1
        "status": StandardStatus.FINAL_STANDARD,
        "pubkey_size_bytes": 1952,  # Standard specification value (FIPS 204 Table 2)
        "ciphertext_size_bytes": None,
        "signature_size_bytes": 3309,  # Standard specification value (FIPS 204 Table 2)
        "library_support": {
            "native_openssl": "OpenSSL 3.5+",
            "oqs_provider": "oqs-provider 0.6.0+",
            "liboqs": "liboqs 0.10.0+",
            "bouncycastle": "BouncyCastle 1.77+",
            "golang_crypto": "Go 1.24+"
        },
        "protocol_support": {
            "tls13": "TLS 1.3 (Signatures)",
            "ssh": "SSHv2",
            "x509": "X.509 Certificates (RFC Draft)",
            "ipsec": "IKEv2"
        },
        "hybrid_support": True,
        "standard_provenance": "NIST FIPS 204 (Specification)",
        "measurement_provenance": "liboqs 0.10.0 / PQC Benchmark Dataset",
        "provenance": "NIST FIPS 204 (Specification) / liboqs Benchmarks",
        "measurement_status": "MEASURED",
        "performance_notes": "NIST recommended primary signature candidate. Measured signature size 3.3KB."
    },
    "ML-DSA-87": {
        "algorithm": "ML-DSA-87",
        "family": "ML-DSA",
        "standard_code": "FIPS 204",
        "primitive": "DIGITAL_SIGNATURE",
        "purposes": [CryptoPurpose.SIGNATURE, CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.AUTHENTICATION],
        "security_objectives": ["integrity", "authentication"],
        "security_level": 5,  # NIST FIPS 204 Table 1
        "status": StandardStatus.FINAL_STANDARD,
        "pubkey_size_bytes": 2592,  # Standard specification value (FIPS 204 Table 2)
        "ciphertext_size_bytes": None,
        "signature_size_bytes": 4627,  # Standard specification value (FIPS 204 Table 2)
        "library_support": {
            "native_openssl": "OpenSSL 3.5+",
            "oqs_provider": "oqs-provider 0.6.0+",
            "liboqs": "liboqs 0.10.0+",
            "bouncycastle": "BouncyCastle 1.77+",
            "golang_crypto": "Go 1.24+"
        },
        "protocol_support": {
            "tls13": "TLS 1.3 (Signatures)",
            "ssh": "SSHv2",
            "x509": "X.509 Certificates (RFC Draft)",
            "ipsec": "IKEv2"
        },
        "hybrid_support": True,
        "standard_provenance": "NIST FIPS 204 (Specification)",
        "measurement_provenance": "liboqs 0.10.0 / PQC Benchmark Dataset",
        "provenance": "NIST FIPS 204 (Specification) / liboqs Benchmarks",
        "measurement_status": "MEASURED",
        "performance_notes": "Maximum security margin. Measured signature size 4.6KB."
    },

    # -------------------------------------------------------------------------
    # STATELESS HASH-BASED SIGNATURE ALGORITHMS (SLH-DSA) - FIPS 205
    # -------------------------------------------------------------------------
    "SLH-DSA-SHA2-128f": {
        "algorithm": "SLH-DSA-SHA2-128f",
        "family": "SLH-DSA",
        "standard_code": "FIPS 205",
        "primitive": "DIGITAL_SIGNATURE",
        "purposes": [CryptoPurpose.SIGNATURE, CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.AUTHENTICATION],
        "security_objectives": ["integrity", "authentication"],
        "security_level": 1,  # NIST FIPS 205 Table 1
        "status": StandardStatus.FINAL_STANDARD,
        "pubkey_size_bytes": 32,  # Standard specification value (FIPS 205 Table 2)
        "ciphertext_size_bytes": None,
        "signature_size_bytes": 17088,  # Standard specification value (FIPS 205 Table 2)
        "library_support": {
            "native_openssl": "UNSUPPORTED_NATIVE",
            "oqs_provider": "oqs-provider 0.6.0+",
            "liboqs": "liboqs 0.10.0+",
            "bouncycastle": "BouncyCastle 1.77+",
            "golang_crypto": "N/A"
        },
        "protocol_support": {
            "tls13": "INCOMPATIBLE_PACKET_SIZE_LIMIT",  # Large signature causes TLS fragmentation issues
            "ssh": "SSHv2 (Limited)",
            "x509": "X.509 Root CA / Firmware Signing",
            "ipsec": "UNSUPPORTED"
        },
        "hybrid_support": False,
        "standard_provenance": "NIST FIPS 205 (Specification)",
        "measurement_provenance": "liboqs 0.10.0 / PQC Benchmark Dataset",
        "provenance": "NIST FIPS 205 (Specification) / liboqs Benchmarks",
        "measurement_status": "MEASURED",
        "performance_notes": "Conservative hash-based signature. Measured public key 32B, signature 17KB."
    },
    "SLH-DSA-SHAKE-128f": {
        "algorithm": "SLH-DSA-SHAKE-128f",
        "family": "SLH-DSA",
        "standard_code": "FIPS 205",
        "primitive": "DIGITAL_SIGNATURE",
        "purposes": [CryptoPurpose.SIGNATURE, CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.AUTHENTICATION],
        "security_objectives": ["integrity", "authentication"],
        "security_level": 1,
        "status": StandardStatus.FINAL_STANDARD,
        "pubkey_size_bytes": 32,
        "ciphertext_size_bytes": None,
        "signature_size_bytes": 17088,
        "library_support": {
            "native_openssl": "UNSUPPORTED_NATIVE",
            "oqs_provider": "oqs-provider 0.6.0+",
            "liboqs": "liboqs 0.10.0+",
            "bouncycastle": "BouncyCastle 1.77+",
            "golang_crypto": "N/A"
        },
        "protocol_support": {
            "tls13": "INCOMPATIBLE_PACKET_SIZE_LIMIT",
            "ssh": "SSHv2 (Limited)",
            "x509": "X.509 Root CA / Firmware Signing",
            "ipsec": "UNSUPPORTED"
        },
        "hybrid_support": False,
        "standard_provenance": "NIST FIPS 205 (Specification)",
        "measurement_provenance": "liboqs 0.10.0 / PQC Benchmark Dataset",
        "provenance": "NIST FIPS 205 (Specification) / liboqs Benchmarks",
        "measurement_status": "MEASURED",
        "performance_notes": "SHAKE-based stateless signature for long-term trust store anchoring."
    },
    "SLH-DSA-SHA2-256f": {
        "algorithm": "SLH-DSA-SHA2-256f",
        "family": "SLH-DSA",
        "standard_code": "FIPS 205",
        "primitive": "DIGITAL_SIGNATURE",
        "purposes": [CryptoPurpose.SIGNATURE, CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.AUTHENTICATION],
        "security_objectives": ["integrity", "authentication"],
        "security_level": 5,
        "status": StandardStatus.FINAL_STANDARD,
        "pubkey_size_bytes": 64,
        "ciphertext_size_bytes": None,
        "signature_size_bytes": 49856,
        "library_support": {
            "native_openssl": "UNSUPPORTED_NATIVE",
            "oqs_provider": "oqs-provider 0.6.0+",
            "liboqs": "liboqs 0.10.0+",
            "bouncycastle": "BouncyCastle 1.77+",
            "golang_crypto": "N/A"
        },
        "protocol_support": {
            "tls13": "INCOMPATIBLE_PACKET_SIZE_LIMIT",
            "ssh": "SSHv2 (Limited)",
            "x509": "X.509 Root CA / Firmware Signing",
            "ipsec": "UNSUPPORTED"
        },
        "hybrid_support": False,
        "standard_provenance": "NIST FIPS 205 (Specification)",
        "measurement_provenance": "liboqs 0.10.0 / PQC Benchmark Dataset",
        "provenance": "NIST FIPS 205 (Specification) / liboqs Benchmarks",
        "measurement_status": "MEASURED",
        "performance_notes": "Level 5 hash-based signature. 49.8KB signature size."
    }
}


def get_candidate(candidate_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve full candidate specification from the authoritative PQC catalog."""
    if not candidate_name:
        return None
    name_clean = candidate_name.strip().upper().replace(" (FIPS 203)", "").replace(" (FIPS 204)", "").replace(" (FIPS 205)", "")
    
    # Direct match
    if name_clean in PQC_CATALOG:
        return PQC_CATALOG[name_clean]
    
    # Alias / Family matching
    for key, cand in PQC_CATALOG.items():
        if key.upper() == name_clean or cand.get("algorithm", "").upper() == name_clean:
            return cand
            
    # Default family mappings
    if name_clean == "ML-KEM":
        return PQC_CATALOG["ML-KEM-768"]
    if name_clean == "ML-DSA":
        return PQC_CATALOG["ML-DSA-65"]
    if name_clean == "SLH-DSA":
        return PQC_CATALOG["SLH-DSA-SHA2-128f"]
    if "HYBRID" in name_clean:
        return PQC_CATALOG["SecP256r1_MLKEM768"]
        
    return None


def get_all_candidates_for_primitive(primitive: str) -> List[Dict[str, Any]]:
    """Return all catalog candidates matching the specified primitive (KEY_ESTABLISHMENT or DIGITAL_SIGNATURE)."""
    prim_upper = primitive.strip().upper()
    matching = []
    for cand in PQC_CATALOG.values():
        cand_prim = cand.get("primitive", "").upper()
        cand_purposes = [p.value if hasattr(p, "value") else str(p).upper() for p in cand.get("purposes", [])]
        if cand_prim == prim_upper or prim_upper in cand_purposes:
            matching.append(cand)
    return matching
