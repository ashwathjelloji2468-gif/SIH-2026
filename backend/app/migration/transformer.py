import os
import re
from typing import Dict, Any, List, Optional
from app.models.enums import CryptoPurpose, QuantumSafety

TRANSFORMATION_PATTERNS = {
    "RSA_TO_ML_DSA": {
        "name": "RSA Signature to NIST FIPS 204 ML-DSA Digital Signature",
        "target": "ML-DSA-65 (NIST FIPS 204)",
        "strategy": "Lattice Signature Replacement",
        "supported_purposes": [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION, CryptoPurpose.UNKNOWN],
        "supported_algorithms": ["RSA", "RSA-2048", "RSA-3072", "RSA-4096", "UNKNOWN"]
    },
    "ECDSA_TO_ML_DSA": {
        "name": "ECDSA to NIST FIPS 204 ML-DSA Digital Signature",
        "target": "ML-DSA-65 (NIST FIPS 204)",
        "strategy": "Lattice Signature Replacement",
        "supported_purposes": [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION, CryptoPurpose.UNKNOWN],
        "supported_algorithms": ["ECDSA", "ECDSA-P256", "ECDSA-P384", "DSA", "ED25519", "UNKNOWN"]
    },
    "RSA_ECDSA_TO_ML_DSA": {
        "name": "RSA/ECDSA to NIST FIPS 204 ML-DSA Digital Signature",
        "target": "ML-DSA-65 (NIST FIPS 204)",
        "strategy": "Lattice Signature Replacement",
        "supported_purposes": [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION, CryptoPurpose.UNKNOWN],
        "supported_algorithms": ["RSA", "ECDSA", "RSA-2048", "ECDSA-P256", "UNKNOWN"]
    },
    "ECDH_TO_ML_KEM": {
        "name": "ECDH to NIST FIPS 203 ML-KEM Key Establishment",
        "target": "ML-KEM-768 (NIST FIPS 203)",
        "strategy": "KEM Key Encapsulation Replacement",
        "supported_purposes": [CryptoPurpose.KEY_ESTABLISHMENT, CryptoPurpose.UNKNOWN],
        "supported_algorithms": ["ECDH", "ECDH-P256", "ECDH-P384", "DH", "X25519", "X448", "UNKNOWN"]
    },
    "ECDH_TO_ML_KEM_HYBRID": {
        "name": "ECDH to NIST FIPS 203 ML-KEM Key Establishment",
        "target": "ML-KEM-768 Hybrid (NIST FIPS 203)",
        "strategy": "KEM Key Encapsulation Replacement",
        "supported_purposes": [CryptoPurpose.KEY_ESTABLISHMENT, CryptoPurpose.UNKNOWN],
        "supported_algorithms": ["ECDH", "ECDH-P256", "ECDH-P384", "DH", "X25519", "X448", "UNKNOWN"]
    }
}

class MigrationTransformer:
    """
    Deterministic Migration Transformer for SENTRIQ.
    Performs real in-place code replacements inside working sandbox directory.
    Returns status: TRANSFORMED, NO_PQC_TRANSFORMATION_REQUIRED, MANUAL_REVIEW_REQUIRED, or BLOCKED.
    """
    def transform_sandbox_code(
        self,
        sandbox_dir: str,
        asset: Any,
        recommendation: Optional[Any] = None,
        requested_pattern: Optional[str] = None
    ) -> Dict[str, Any]:

        alg_upper = (getattr(asset, "algorithm_name", "") or "").strip().upper()
        purpose = getattr(asset, "purpose", CryptoPurpose.UNKNOWN)
        location = getattr(asset, "location", "")
        asset_type_str = asset.asset_type.value if hasattr(asset, "asset_type") and hasattr(asset.asset_type, "value") else str(getattr(asset, "asset_type", "ALGORITHM"))

        rec_category = str(getattr(recommendation, "category", "") or "").upper()
        target_pqc = str(getattr(recommendation, "target_pqc_candidate", "") or "").upper()

        # Check CASE 4: Unknown / custom / HSM / vendor / binary-only -> MANUAL_REVIEW_REQUIRED
        is_unknown_or_complex = (
            purpose == CryptoPurpose.UNKNOWN or
            alg_upper in ["UNKNOWN", "CUSTOM_CIPHER", "PROPRIETARY_HSM_CIPHER"] or
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

        # Determine pattern key
        pattern_key = requested_pattern
        if not pattern_key:
            if isinstance(recommendation, dict) and recommendation.get("transformation_pattern"):
                pattern_key = recommendation.get("transformation_pattern")
            elif hasattr(recommendation, "transformation_pattern") and getattr(recommendation, "transformation_pattern"):
                pattern_key = getattr(recommendation, "transformation_pattern")

        if not pattern_key:
            if purpose == CryptoPurpose.KEY_ESTABLISHMENT or any(k in alg_upper for k in ["ECDH", "DH", "X25519", "X448"]):
                pattern_key = "ECDH_TO_ML_KEM_HYBRID"
            elif purpose in [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION] or any(k in alg_upper for k in ["RSA", "ECDSA", "DSA", "ED25519"]):
                pattern_key = "RSA_TO_ML_DSA" if "RSA" in alg_upper else "ECDSA_TO_ML_DSA"

        if not pattern_key or pattern_key not in TRANSFORMATION_PATTERNS:
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

        # Check pattern compatibility with asset (Requirement 4 & 12)
        is_key_ex_pattern = "ECDH" in pattern_key or "KEM" in pattern_key
        is_key_ex_asset = purpose == CryptoPurpose.KEY_ESTABLISHMENT or any(k in alg_upper for k in ["ECDH", "DH", "X25519", "X448"])
        is_sig_pattern = "DSA" in pattern_key or "RSA" in pattern_key
        is_sig_asset = purpose in [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION] or any(k in alg_upper for k in ["RSA", "ECDSA", "DSA"])

        if is_key_ex_pattern and is_sig_asset and not is_key_ex_asset:
            return {
                "status": "BLOCKED",
                "transformation_type": pattern_key,
                "strategy": pattern["strategy"],
                "files_considered": [location] if location else [],
                "files_changed": [],
                "unsupported_assumptions": [f"Incompatible migration pattern '{pattern_key}' requested for signature asset '{alg_upper}'."],
                "changes_summary": {"reason": "Migration pattern is incompatible with asset cryptographic purpose."}
            }

        if is_sig_pattern and is_key_ex_asset and not is_sig_asset:
            return {
                "status": "BLOCKED",
                "transformation_type": pattern_key,
                "strategy": pattern["strategy"],
                "files_considered": [location] if location else [],
                "files_changed": [],
                "unsupported_assumptions": [f"Incompatible migration pattern '{pattern_key}' requested for key-establishment asset '{alg_upper}'."],
                "changes_summary": {"reason": "Migration pattern is incompatible with asset cryptographic purpose."}
            }

        # Locate target file inside working sandbox directory
        target_file_in_sandbox = None
        files_considered = []

        if location:
            clean_loc = os.path.basename(location) if os.path.isabs(location) else location.lstrip("/")
            possible_path = os.path.join(sandbox_dir, clean_loc)
            if os.path.exists(possible_path) and os.path.isfile(possible_path):
                target_file_in_sandbox = possible_path
            else:
                for root, _, files in os.walk(sandbox_dir):
                    for f in files:
                        if f == clean_loc or f == os.path.basename(location):
                            target_file_in_sandbox = os.path.join(root, f)
                            break
                    if target_file_in_sandbox:
                        break

        if not target_file_in_sandbox:
            for root, _, files in os.walk(sandbox_dir):
                for f in sorted(files):
                    if f.endswith((".py", ".js", ".ts", ".java", ".go", ".rs")):
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
            with open(target_file_in_sandbox, "r", errors="ignore") as f:
                content = f.read()

            transformed_content = content
            replaced = False

            if "ECDH" in pattern_key or "KEM" in pattern_key:
                # Deterministic ECDH -> ML-KEM replacement
                # Replace imports
                if "from cryptography.hazmat.primitives.asymmetric import ec" in transformed_content:
                    transformed_content = transformed_content.replace(
                        "from cryptography.hazmat.primitives.asymmetric import ec",
                        "from pqcrypto.kem.ml_kem_768 import generate_keypair, encrypt, decrypt  # ML-KEM-768 (FIPS 203)"
                    )
                    replaced = True
                elif "import ec" in transformed_content:
                    transformed_content = transformed_content.replace(
                        "import ec",
                        "from pqcrypto.kem.ml_kem_768 import generate_keypair, encrypt, decrypt  # ML-KEM-768 (FIPS 203)"
                    )
                    replaced = True

                # Replace full block if present (e.g. derive_shared_secret)
                ecdh_block_pattern = r"private_key\s*=\s*ec\.generate_private_key\(ec\.SECP256R1\(\)\)\s*\n\s*peer_public_key\s*=\s*ec\.generate_private_key\(ec\.SECP256R1\(\)\)\.public_key\(\)\s*\n\s*shared_key\s*=\s*private_key\.exchange\(ec\.ECDH\(\),\s*peer_public_key\)"
                if re.search(ecdh_block_pattern, transformed_content):
                    transformed_content = re.sub(
                        ecdh_block_pattern,
                        "public_key, secret_key = generate_keypair()\n    ciphertext, shared_secret_sender = encrypt(public_key)\n    shared_secret_receiver = decrypt(secret_key, ciphertext)\n    shared_key = shared_secret_receiver",
                        transformed_content
                    )
                    replaced = True
                else:
                    # Fallback line-by-line replacements
                    if "ec.generate_private_key(ec.SECP256R1())" in transformed_content:
                        transformed_content = transformed_content.replace(
                            "ec.generate_private_key(ec.SECP256R1())",
                            "generate_keypair()"
                        )
                        replaced = True
                    if "private_key.exchange(ec.ECDH(), peer_public_key)" in transformed_content:
                        transformed_content = transformed_content.replace(
                            "private_key.exchange(ec.ECDH(), peer_public_key)",
                            "decrypt(secret_key, ciphertext)"
                        )
                        replaced = True
                    elif ".exchange(" in transformed_content:
                        transformed_content = re.sub(
                            r"\b\w+\.exchange\([^)]*\)",
                            "decrypt(secret_key, ciphertext)",
                            transformed_content
                        )
                        replaced = True

            elif "RSA" in pattern_key or "ECDSA" in pattern_key or "DSA" in pattern_key:
                # Deterministic RSA/ECDSA -> ML-DSA replacement
                # Replace imports
                if "from cryptography.hazmat.primitives.asymmetric import rsa, padding" in transformed_content:
                    transformed_content = transformed_content.replace(
                        "from cryptography.hazmat.primitives.asymmetric import rsa, padding",
                        "from pqcrypto.sign import ml_dsa_65  # ML-DSA-65 (FIPS 204)"
                    )
                    replaced = True
                elif "from cryptography.hazmat.primitives.asymmetric import rsa" in transformed_content:
                    transformed_content = transformed_content.replace(
                        "from cryptography.hazmat.primitives.asymmetric import rsa",
                        "from pqcrypto.sign import ml_dsa_65"
                    )
                    replaced = True
                elif "from cryptography.hazmat.primitives.asymmetric import ec" in transformed_content:
                    transformed_content = transformed_content.replace(
                        "from cryptography.hazmat.primitives.asymmetric import ec",
                        "from pqcrypto.sign import ml_dsa_65"
                    )
                    replaced = True
                elif "import rsa" in transformed_content:
                    transformed_content = transformed_content.replace(
                        "import rsa",
                        "from pqcrypto.sign import ml_dsa_65"
                    )
                    replaced = True

                # Replace key generation
                if "rsa.generate_private_key(public_exponent=65537, key_size=2048)" in transformed_content:
                    transformed_content = transformed_content.replace(
                        "rsa.generate_private_key(public_exponent=65537, key_size=2048)",
                        "ml_dsa_65.generate_keypair()"
                    )
                    replaced = True
                elif "rsa.generate_key()" in transformed_content:
                    transformed_content = transformed_content.replace(
                        "rsa.generate_key()",
                        "ml_dsa_65.generate_keypair()"
                    )
                    replaced = True
                elif "rsa.generate_private_key" in transformed_content:
                    transformed_content = re.sub(
                        r"rsa\.generate_private_key\([^\n]*\)",
                        "ml_dsa_65.generate_keypair()",
                        transformed_content
                    )
                    replaced = True
                elif "ec.generate_private_key" in transformed_content:
                    transformed_content = re.sub(
                        r"ec\.generate_private_key\([^\n]*\)",
                        "ml_dsa_65.generate_keypair()",
                        transformed_content
                    )
                    replaced = True

                # Replace signature call
                if "private_key.sign(" in transformed_content:
                    transformed_content = re.sub(
                        r"private_key\.sign\([^\n]*\)",
                        "ml_dsa_65.sign(secret_key, data)",
                        transformed_content
                    )
                    replaced = True
                elif "RS256" in transformed_content:
                    transformed_content = transformed_content.replace("RS256", "ML-DSA-65")
                    replaced = True

            if not replaced or transformed_content == content:
                # If no vulnerable pattern matches or file remains identical -> MANUAL_REVIEW_REQUIRED
                return {
                    "status": "MANUAL_REVIEW_REQUIRED",
                    "transformation_type": pattern_key,
                    "target_pqc_candidate": pattern["target"],
                    "strategy": pattern["strategy"],
                    "files_considered": list(set(files_considered)),
                    "files_changed": [],
                    "unsupported_assumptions": ["Safe deterministic transformation could not be established in target file."],
                    "changes_summary": {"reason": "Source code contains no matching vulnerable operation for automated replacement."}
                }

            with open(target_file_in_sandbox, "w") as f:
                f.write(transformed_content)

            files_changed = [rel_changed_path]

            return {
                "status": "TRANSFORMED",
                "transformation_type": pattern_key,
                "target_pqc_candidate": pattern["target"],
                "strategy": pattern["strategy"],
                "files_considered": list(set(files_considered)),
                "files_changed": files_changed,
                "unsupported_assumptions": [],
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

