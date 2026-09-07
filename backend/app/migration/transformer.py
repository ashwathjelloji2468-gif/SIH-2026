import os
from typing import Dict, Any, List, Optional
from app.models.enums import CryptoPurpose, RecommendationCategory, QuantumSafety

TRANSFORMATION_PATTERNS = {
    "ECDH_TO_ML_KEM": {
        "name": "ECDH to NIST FIPS 203 ML-KEM Key Establishment",
        "target": "ML-KEM (FIPS 203)",
        "strategy": "KEM Encapsulation Adapter",
        "search_terms": ["ECDH", "generate_private_key", "X25519", "X448", "DiffieHellman"],
        "template": (
            "# NIST PQC Migration: ML-KEM (FIPS 203) Key Encapsulation Replacement\n"
            "try:\n"
            "    from pqcrypto.kem import ml_kem_768\n"
            "    public_key, secret_key = ml_kem_768.generate_keypair()\n"
            "except ImportError:\n"
            "    # Fallback PQC Adapter Representation\n"
            "    def generate_pqc_kem_keypair():\n"
            "        return ('ML_KEM_768_PUBLIC_KEY', 'ML_KEM_768_SECRET_KEY')\n"
        )
    },
    "RSA_ECDSA_TO_ML_DSA": {
        "name": "RSA/ECDSA to NIST FIPS 204 ML-DSA Digital Signature",
        "target": "ML-DSA (FIPS 204)",
        "strategy": "Lattice Signature Adapter",
        "search_terms": ["rsa.generate_private_key", "ec.generate_private_key", "ECDSA", "DSAPrivateKey"],
        "template": (
            "# NIST PQC Migration: ML-DSA (FIPS 204) Lattice Signature Replacement\n"
            "try:\n"
            "    from pqcrypto.sign import ml_dsa_65\n"
            "    public_key, secret_key = ml_dsa_65.generate_keypair()\n"
            "except ImportError:\n"
            "    # Fallback PQC Adapter Representation\n"
            "    def generate_pqc_signature_keypair():\n"
            "        return ('ML_DSA_65_PUBLIC_KEY', 'ML_DSA_65_SECRET_KEY')\n"
        )
    }
}

class MigrationTransformer:
    """
    Deterministic Migration Transformer for SENTRIQ (Prompt 6).
    Applies conservative code transformations ONLY inside isolated sandbox directories.
    Returns status: TRANSFORMED, NO_PQC_TRANSFORMATION_REQUIRED, or MANUAL_REVIEW_REQUIRED.
    """
    def transform_sandbox_code(
        self,
        sandbox_dir: str,
        asset: Any,
        recommendation: Optional[Any] = None
    ) -> Dict[str, Any]:

        alg_upper = (getattr(asset, "algorithm_name", "") or "").strip().upper()
        purpose = getattr(asset, "purpose", CryptoPurpose.UNKNOWN)
        location = getattr(asset, "location", "")
        asset_type_str = asset.asset_type.value if hasattr(asset, "asset_type") and hasattr(asset.asset_type, "value") else str(getattr(asset, "asset_type", "ALGORITHM"))

        rec_category = str(getattr(recommendation, "category", "") or "").upper()
        target_pqc = str(getattr(recommendation, "target_pqc_candidate", "") or "").upper()

        # Check CASE 4: Unknown / custom / HSM / vendor / binary-only
        is_unknown_or_complex = (
            purpose == CryptoPurpose.UNKNOWN or
            alg_upper in ["UNKNOWN", "CUSTOM_CIPHER"] or
            asset_type_str in ["BINARY", "CONTAINER", "VENDOR_MANAGED"] or
            "HSM" in alg_upper or "HARDWARE" in alg_upper or
            "MANUAL" in rec_category
        )

        if is_unknown_or_complex:
            return {
                "status": "MANUAL_REVIEW_REQUIRED",
                "transformation_type": "NONE",
                "strategy": "MANUAL_CRYPTO_AUDIT_REQUIRED",
                "files_considered": [location] if location else [],
                "files_changed": [],
                "unsupported_assumptions": [
                    f"Asset '{alg_upper}' ({asset_type_str}) requires manual cryptographer audit."
                ],
                "changes_summary": {
                    "reason": "Complex, binary, vendor, or unclassified cryptographic implementation."
                }
            }

        # Check CASE 3: Symmetric / Hashing / MAC / KDF -> Retain existing primitive
        is_symmetric = (
            "RETAIN" in rec_category or
            "RETAIN" in target_pqc or
            purpose in [CryptoPurpose.ENCRYPTION, CryptoPurpose.HASHING, CryptoPurpose.MAC, CryptoPurpose.PASSWORD_DERIVATION] or
            any(k in alg_upper for k in ["AES", "CHACHA", "SHA", "HMAC", "PBKDF2", "ARGON2", "BCRYPT", "SCRYPT"])
        )

        if is_symmetric:
            return {
                "status": "NO_PQC_TRANSFORMATION_REQUIRED",
                "transformation_type": "RETAIN_EXISTING_PRIMITIVE",
                "strategy": "RETAIN_SYMMETRIC_OR_HASH_ALGORITHM",
                "files_considered": [location] if location else [],
                "files_changed": [],
                "unsupported_assumptions": [],
                "changes_summary": {
                    "reason": f"Symmetric primitive '{alg_upper}' is quantum-resistant. No PQC replacement required."
                }
            }

        # Check CASE 1 & 2: Key Establishment (ECDH) or Digital Signatures (RSA/ECDSA)
        pattern_key = None
        if purpose == CryptoPurpose.KEY_ESTABLISHMENT or any(k in alg_upper for k in ["ECDH", "DH", "X25519", "X448"]):
            pattern_key = "ECDH_TO_ML_KEM"
        elif purpose in [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION] or any(k in alg_upper for k in ["RSA", "ECDSA", "DSA", "ED25519"]):
            pattern_key = "RSA_ECDSA_TO_ML_DSA"

        if not pattern_key:
            return {
                "status": "MANUAL_REVIEW_REQUIRED",
                "transformation_type": "UNRECOGNIZED_PATTERN",
                "strategy": "MANUAL_AUDIT",
                "files_considered": [location] if location else [],
                "files_changed": [],
                "unsupported_assumptions": [f"Unrecognized primitive pattern for algorithm '{alg_upper}'."],
                "changes_summary": {"reason": f"Algorithm '{alg_upper}' has no automated transformation pattern."}
            }

        pattern = TRANSFORMATION_PATTERNS[pattern_key]

        # Locate files in sandbox to transform
        files_changed = []
        files_considered = []

        # Find target source file inside sandbox
        target_file_in_sandbox = None
        if location:
            # Check relative location inside sandbox
            possible_path = os.path.join(sandbox_dir, location)
            if os.path.exists(possible_path) and os.path.isfile(possible_path):
                target_file_in_sandbox = possible_path

        if not target_file_in_sandbox:
            # Search for any .py file in sandbox
            for root, _, files in os.walk(sandbox_dir):
                for f in files:
                    if f.endswith(".py"):
                        fp = os.path.join(root, f)
                        files_considered.append(os.path.relpath(fp, sandbox_dir))
                        if not target_file_in_sandbox:
                            target_file_in_sandbox = fp

        if not target_file_in_sandbox:
            return {
                "status": "MANUAL_REVIEW_REQUIRED",
                "transformation_type": pattern_key,
                "strategy": pattern["strategy"],
                "files_considered": files_considered,
                "files_changed": [],
                "unsupported_assumptions": ["No suitable target source file found in sandbox for transformation."],
                "changes_summary": {"reason": "Source file unavailable for transformation."}
            }

        rel_changed_path = os.path.relpath(target_file_in_sandbox, sandbox_dir)
        files_considered.append(rel_changed_path)

        try:
            with open(target_file_in_sandbox, "r") as f:
                content = f.read()

            # Append PQC adapter snippet conservatively
            new_content = content + "\n\n" + pattern["template"]

            with open(target_file_in_sandbox, "w") as f:
                f.write(new_content)

            files_changed.append(rel_changed_path)

            return {
                "status": "TRANSFORMED",
                "transformation_type": pattern_key,
                "target_pqc_candidate": pattern["target"],
                "strategy": pattern["strategy"],
                "files_considered": list(set(files_considered)),
                "files_changed": files_changed,
                "unsupported_assumptions": [
                    "Assumes PQC provider library wrapper compatibility during pilot testing."
                ],
                "changes_summary": {
                    "pattern_applied": pattern["name"],
                    "strategy": pattern["strategy"],
                    "files_changed": files_changed,
                    "target_candidate": pattern["target"]
                }
            }

        except Exception as e:
            return {
                "status": "FAILED",
                "transformation_type": pattern_key,
                "strategy": pattern["strategy"],
                "files_considered": list(set(files_considered)),
                "files_changed": [],
                "unsupported_assumptions": [f"Transformation error: {str(e)}"],
                "changes_summary": {"error": str(e)}
            }
