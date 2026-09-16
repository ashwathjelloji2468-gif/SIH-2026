"""
Dedicated Z Engine — Component-Wise Quantum Exposure Engine for SENTRIQ.

Evaluates Z_i (quantum threat deadline for cryptographic component i)
under a configurable CRQC threat horizon T_Q (default: 10 years).

Canonical Semantic Contract:
- Z_i (value_years_remaining): remaining years until the component's quantum threat/deadline.
- target_year: calendar year for reference (CURRENT_YEAR + Z_i when numeric).
- Z_i is numeric ONLY for deadline-based components (Shor-vulnerable public key, legacy deprecated ciphers).
- For non-deadline components (AES-256, SHA-256, ML-KEM), value_years_remaining is None.
"""

from typing import Dict, Any, List, Optional, Tuple

DEFAULT_QUANTUM_HORIZON = 10  # T_Q = 10 years (relative horizon: ~2036 for 2026)
CURRENT_YEAR = 2026

# Enums / Literal Constants
QUANTUM_CLASS_SHOR = "SHOR_VULNERABLE"
QUANTUM_CLASS_STRENGTH_REDUCTION = "QUANTUM_STRENGTH_REDUCTION"
QUANTUM_CLASS_PQC = "PQC_RESISTANT"
QUANTUM_CLASS_HYBRID = "HYBRID"
QUANTUM_CLASS_UNKNOWN = "UNKNOWN"

STATUS_VULNERABLE_AT_HORIZON = "VULNERABLE_AT_HORIZON"
STATUS_UNACCEPTABLE_AT_HORIZON = "QUANTUM_UNACCEPTABLE_AT_HORIZON"
STATUS_REDUCED_BUT_ACCEPTABLE = "REDUCED_BUT_ACCEPTABLE"
STATUS_REQUIRES_REVIEW = "REQUIRES_REVIEW"
STATUS_NO_IMMEDIATE_DEADLINE = "NO_IMMEDIATE_QUANTUM_DEADLINE"


class ZEngine:
    """
    Component-wise Quantum Exposure Engine (Z Engine).
    Calculates component-specific quantum deadlines (Z_i) and quantum impact classification.
    """

    def __init__(self, default_horizon: int = DEFAULT_QUANTUM_HORIZON):
        self.default_horizon = default_horizon

    def _calculate_base_score(
        self,
        primitive: str,
        algorithm_name: str,
        purpose: str = "",
        asset_type: str = ""
    ) -> float:
        text = f"{primitive} {algorithm_name} {purpose} {asset_type}".upper().strip()

        # Signature -> 4.0
        sig_keywords = ["SIGNATURE", "SIG", "ECDSA", "ED25519", "SLH-DSA", "ML-DSA", "DILITHIUM", "FALCON", "SPHINCS", "DSA"]
        if any(kw in text for kw in sig_keywords) or "SIGN" in text:
            return 4.0

        # Key Exchange / Asymmetric / Certificate / Public Key -> 5.0
        key_keywords = [
            "RSA", "ECC", "ECDH", "DH", "DIFFIE", "X25519", "KEY_EXCHANGE", "KEY_ESTABLISHMENT",
            "ASYMMETRIC", "CERTIFICATE", "CERT", "X509", "PUBLIC_KEY", "ML-KEM", "KYBER", "PQC"
        ]
        if any(kw in text for kw in key_keywords):
            return 5.0

        # Hash / Symmetric -> 1.0
        sym_keywords = [
            "AES", "SHA", "DES", "3DES", "CHACHA", "SALSA", "BLOWFISH", "HMAC", "MD5",
            "HASH", "SYMMETRIC", "CIPHER"
        ]
        if any(kw in text for kw in sym_keywords):
            return 1.0

        return 1.0

    def _calculate_env_multiplier(
        self,
        execution_environment: str = "",
        location: str = ""
    ) -> float:
        text = f"{execution_environment} {location}".upper().strip()
        if any(kw in text for kw in ["EMBEDDED", "IOT", "FIRMWARE"]):
            return 4.0
        if any(kw in text for kw in ["HARDWARE", "HSM"]):
            return 3.0
        if any(kw in text for kw in ["ON_PREM", "ON-PREM", "ONPREM", "SERVER"]):
            return 2.0
        return 1.0

    def _calculate_dep_factor(self, crypto_refs: Optional[List[Any]] = None) -> float:
        refs = crypto_refs or []
        count = len(refs) if isinstance(refs, list) else 0
        return 1.0 + 0.1 * count

    def evaluate_component(
        self,
        component: Dict[str, Any],
        quantum_horizon: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single cryptographic component.
        Returns canonical ZResult dict with consistent Z_i (value_years_remaining) and target_year.
        """
        comp_id = str(component.get("id") or component.get("component_id") or component.get("name") or "unknown-component")
        algo_name = str(component.get("algorithm_name") or component.get("algorithm") or component.get("primitive") or "").strip()
        primitive = str(component.get("primitive") or algo_name).strip()
        purpose = str(component.get("purpose") or "")
        asset_type = str(component.get("asset_type") or "")
        exec_env = str(component.get("execution_environment") or component.get("environment") or "")
        refs = component.get("cryptoRefArray") or component.get("dependencies") or component.get("crypto_ref_array") or []

        key_size = component.get("key_size")
        if isinstance(key_size, str) and key_size.isdigit():
            key_size = int(key_size)
        elif not isinstance(key_size, int):
            key_size = None

        if key_size is None:
            text_for_size = f"{algo_name} {primitive}".upper()
            import re
            m = re.search(r'(4096|3072|2048|1024|521|384|256|192)', text_for_size)
            if m:
                key_size = int(m.group(1))

        output_size = component.get("output_size")
        if isinstance(output_size, str) and output_size.isdigit():
            output_size = int(output_size)
        elif not isinstance(output_size, int):
            output_size = None

        location = str(component.get("location") or component.get("repository_path") or "")

        t_q = quantum_horizon if quantum_horizon is not None and quantum_horizon > 0 else self.default_horizon

        base_score = self._calculate_base_score(primitive, algo_name, purpose, asset_type)
        env_mult = self._calculate_env_multiplier(exec_env, location)
        dep_factor = self._calculate_dep_factor(refs)
        z_score = base_score * env_mult * dep_factor

        # Component-wise classification & artifact-specific Z_i calculation
        q_class, status, raw_z_value, c_bits, q_bits, explanation, confidence = self._classify_component(
            primitive=primitive,
            algorithm_name=algo_name,
            key_size=key_size,
            output_size=output_size,
            t_q=t_q,
            purpose=purpose,
            asset_type=asset_type,
            execution_environment=exec_env,
            location=location,
            crypto_refs=refs
        )

        z_value = raw_z_value
        if z_value is not None:
            z_value = float(z_value)
            z_planning_horizon_years = z_value
            z_target_year = CURRENT_YEAR + int(round(z_value))
        else:
            z_planning_horizon_years = None
            z_target_year = None

        return {
            "component_id": comp_id,
            "primitive": primitive or algo_name or "UNKNOWN",
            "algorithm": algo_name or primitive or "UNKNOWN",
            "key_size": key_size,
            "location": location,
            "quantum_class": q_class,
            "classification": q_class,
            "status": status,
            "z_value": z_value,
            "value_years_remaining": z_value,
            "z_score": round(z_score, 2),
            "z_planning_horizon_years": z_planning_horizon_years,
            "quantum_horizon": z_planning_horizon_years,
            "z_target_year": z_target_year,
            "target_year": z_target_year,
            "target_horizon_year": z_target_year,
            "base_score": base_score,
            "env_multiplier": env_mult,
            "dep_factor": round(dep_factor, 2),
            "classical_security_bits": c_bits,
            "quantum_security_bits": q_bits,
            "explanation": explanation,
            "rationale": explanation,
            "confidence": confidence,
            "metadata": {
                "model": "CANONICAL_Z_ENGINE",
                "current_year": CURRENT_YEAR,
                "threat_horizon_year": z_target_year,
                "disclaimer": "Component-wise relative Z_i deadline."
            }
        }

    def _classify_component(
        self,
        primitive: str,
        algorithm_name: str,
        key_size: Optional[int],
        output_size: Optional[int],
        t_q: int,
        purpose: str = "",
        asset_type: str = "",
        execution_environment: str = "",
        location: str = "",
        crypto_refs: Optional[List[Any]] = None
    ) -> Tuple[str, str, Optional[float], Optional[int], Optional[int], str, str]:
        text = f"{primitive} {algorithm_name}".upper().strip()

        if not algorithm_name and not primitive:
            return (
                QUANTUM_CLASS_UNKNOWN,
                STATUS_REQUIRES_REVIEW,
                None,
                None,
                None,
                "Insufficient information to confidently determine quantum exposure. Manual cryptographic review required.",
                "LOW"
            )

        # Category D: Hybrid / Composite Primitives
        if any(h in text for h in ["HYBRID", "COMPOSITE"]) or ("+" in text and any(p in text for p in ["ML-KEM", "KYBER", "DILITHIUM", "ML-DSA"])):
            return (
                QUANTUM_CLASS_HYBRID,
                STATUS_REDUCED_BUT_ACCEPTABLE,
                None,
                256,
                128,
                "Hybrid composite primitive combining classical public-key and post-quantum algorithms. Provides transition-period defense-in-depth.",
                "HIGH"
            )

        # Category C: Post-Quantum Cryptography (PQC)
        pqc_keywords = ["ML-KEM", "KYBER", "ML-DSA", "DILITHIUM", "SLH-DSA", "SPHINCS", "FALCON", "LMS", "HSS", "NTRU", "FRODOKEM", "BIKE", "HQC", "MCELIECE", "PQC"]
        if any(kw in text for kw in pqc_keywords):
            return (
                QUANTUM_CLASS_PQC,
                STATUS_NO_IMMEDIATE_DEADLINE,
                None,
                256,
                256,
                "Post-quantum cryptographic primitive (NIST PQC standard/candidate). No immediate CRQC deadline assigned.",
                "HIGH"
            )

        # Category A: Public-key algorithms vulnerable to Shor's algorithm
        shor_keywords = [
            "RSA", "ECC", "ECDSA", "ECDH", "DSA", "DH", "DIFFIE", "ELGAMAL",
            "X25519", "ED25519", "SECP256K1", "SECP384R1", "SECP521R1", "PRIME256V1", "EC",
            "CERTIFICATE", "X509"
        ]
        if any(kw in text for kw in shor_keywords):
            classical_bits = 112
            ref_bits = 112.0
            if any(e in text for e in ["ECDSA", "ECDH", "ECC", "25519", "SECP", "PRIME", "EC"]):
                ref_bits = 128.0
                if key_size:
                    if key_size <= 192:
                        classical_bits = 96
                    elif key_size <= 256:
                        classical_bits = 128
                    elif key_size <= 384:
                        classical_bits = 192
                    elif key_size >= 521:
                        classical_bits = 256
                    else:
                        classical_bits = 128
                else:
                    if "384" in text:
                        classical_bits = 192
                    elif "521" in text:
                        classical_bits = 256
                    else:
                        classical_bits = 128
            elif "RSA" in text or "DSA" in text or "DH" in text:
                ref_bits = 112.0
                if key_size:
                    if key_size <= 1024:
                        classical_bits = 80
                    elif key_size <= 2048:
                        classical_bits = 112
                    elif key_size <= 3072:
                        classical_bits = 128
                    else:
                        classical_bits = 144

            # Calculate artifact-specific Z_i for Shor-vulnerable components
            z_bits = float(t_q) * (float(classical_bits) / ref_bits)

            # Purpose adjustment (e.g. HNDL risk for key exchange / encryption when explicitly specified)
            purpose_text = f"{purpose} {primitive} {algorithm_name}".upper().strip()
            purpose_offset = 0.0
            if any(k in purpose_text for k in ["ECDH", "DH", "KEY_EXCHANGE", "KEY_AGREEMENT", "HNDL"]):
                if not any(s in purpose_text for s in ["ECDSA", "SIGNATURE", "PSS"]):
                    purpose_offset = -1.0

            # Environment adjustment
            env_text = f"{execution_environment} {location}".upper()
            env_offset = 0.0
            if any(k in env_text for k in ["EMBEDDED", "IOT", "FIRMWARE"]):
                env_offset = -0.5

            # Dependency adjustment
            dep_offset = 0.0
            if crypto_refs and isinstance(crypto_refs, list) and len(crypto_refs) > 2:
                dep_offset = -0.5

            raw_z_value = round(max(1.0, z_bits + purpose_offset + env_offset + dep_offset), 1)

            return (
                QUANTUM_CLASS_SHOR,
                STATUS_VULNERABLE_AT_HORIZON,
                raw_z_value,
                classical_bits,
                0,
                f"Fundamental public-key exposure: Dependent on prime factorization / discrete logarithms, vulnerable to polynomial-time quantum attack (Shor's algorithm). Component quantum deadline Z_i = {raw_z_value} years (~{CURRENT_YEAR + int(round(raw_z_value))}).",
                "HIGH"
            )

        # Category B: Symmetric Ciphers & Hash Functions (Grover / BHT reduction)
        # Sub-case B1: Legacy / Weak Primitives
        legacy_keywords = ["DES", "3DES", "RC4", "MD5", "SHA1", "SHA-1", "BLOWFISH"]
        if any(kw in text for kw in legacy_keywords):
            raw_z_value = float(t_q)
            return (
                QUANTUM_CLASS_STRENGTH_REDUCTION,
                STATUS_UNACCEPTABLE_AT_HORIZON,
                raw_z_value,
                64 if ("DES" in text or "MD5" in text) else 80,
                32 if ("DES" in text or "MD5" in text) else 40,
                f"Security-strength reduction: Primitive is legacy/deprecated classically and further degraded under Grover/BHT quantum algorithms. Component quantum deadline Z_i = {raw_z_value} years (~{CURRENT_YEAR + int(round(raw_z_value))}).",
                "HIGH"
            )

        # Sub-case B2: AES / ChaCha / Symmetric
        if "AES" in text or "CHACHA" in text or "SALSA" in text:
            actual_key_size = key_size or (128 if "128" in text else (192 if "192" in text else (256 if "256" in text else 256)))
            quantum_bits = int(actual_key_size / 2)

            if actual_key_size < 192:
                # AES-128 -> ~64 bits quantum security
                return (
                    QUANTUM_CLASS_STRENGTH_REDUCTION,
                    STATUS_REQUIRES_REVIEW,
                    None,
                    actual_key_size,
                    quantum_bits,
                    f"Security-strength reduction: Grover's search algorithm halves effective key length from {actual_key_size} bits to ~{quantum_bits} bits. Requires policy review against organizational 128-bit quantum security standards.",
                    "HIGH"
                )
            else:
                # AES-256 / AES-192 -> ~128 / ~96 bits quantum security
                return (
                    QUANTUM_CLASS_STRENGTH_REDUCTION,
                    STATUS_REDUCED_BUT_ACCEPTABLE,
                    None,
                    actual_key_size,
                    quantum_bits,
                    f"Security-strength reduction: Quantum search (Grover's algorithm) reduces effective security from {actual_key_size} bits to ~{quantum_bits} bits. This remains acceptable under current post-quantum security baselines.",
                    "HIGH"
                )

        # Sub-case B3: Hashes & MACs (SHA-2, SHA-3, HMAC, Argon2, Blake2)
        hash_keywords = ["SHA2", "SHA256", "SHA-256", "SHA384", "SHA-384", "SHA512", "SHA-512", "SHA3", "HMAC", "BLAKE2", "ARGON2", "PBKDF2"]
        if any(kw in text for kw in hash_keywords):
            bits = output_size or (512 if any(s in text for s in ["512", "384"]) else 256)
            q_bits = int(bits / 2)
            return (
                QUANTUM_CLASS_STRENGTH_REDUCTION,
                STATUS_REDUCED_BUT_ACCEPTABLE,
                None,
                bits,
                q_bits,
                f"Security-strength reduction: Hash collision and preimage resistance are reduced under Grover/BHT quantum algorithms (effective ~{q_bits} bits), but maintains adequate security strength for general applications.",
                "HIGH"
            )

        # Fallback / Unknown
        return (
            QUANTUM_CLASS_UNKNOWN,
            STATUS_REQUIRES_REVIEW,
            None,
            None,
            None,
            "Insufficient information to confidently determine quantum exposure. Manual cryptographic review required.",
            "LOW"
        )

    def evaluate_asset(self, asset: Any, quantum_horizon: Optional[int] = None) -> Dict[str, Any]:
        """Convert a CryptoAsset model instance or dictionary into a component and evaluate."""
        if hasattr(asset, "__dict__"):
            comp_dict = {
                "id": str(getattr(asset, "id", "")),
                "primitive": getattr(asset, "algorithm_name", ""),
                "algorithm_name": getattr(asset, "algorithm_name", ""),
                "key_size": getattr(asset, "key_size", None),
                "location": getattr(asset, "location", ""),
                "purpose": getattr(asset, "purpose", ""),
                "execution_environment": getattr(asset, "execution_environment", None) or getattr(asset, "environment", None),
                "cryptoRefArray": getattr(asset, "cryptoRefArray", None) or getattr(asset, "dependencies", None),
                "asset_type": str(getattr(asset, "asset_type", ""))
            }
        elif isinstance(asset, dict):
            comp_dict = asset
        else:
            comp_dict = {"id": str(asset)}

        return self.evaluate_component(comp_dict, quantum_horizon=quantum_horizon)

    def evaluate_project(
        self,
        assets: List[Any],
        quantum_horizon: Optional[int] = None
    ) -> Dict[str, Any]:
        """Evaluate all cryptographic components in a project."""
        t_q = quantum_horizon if quantum_horizon is not None and quantum_horizon > 0 else self.default_horizon
        results = [self.evaluate_asset(asset, quantum_horizon=t_q) for asset in assets]

        class_breakdown = {
            QUANTUM_CLASS_SHOR: 0,
            QUANTUM_CLASS_STRENGTH_REDUCTION: 0,
            QUANTUM_CLASS_PQC: 0,
            QUANTUM_CLASS_HYBRID: 0,
            QUANTUM_CLASS_UNKNOWN: 0
        }
        status_breakdown = {
            STATUS_VULNERABLE_AT_HORIZON: 0,
            STATUS_UNACCEPTABLE_AT_HORIZON: 0,
            STATUS_REDUCED_BUT_ACCEPTABLE: 0,
            STATUS_REQUIRES_REVIEW: 0,
            STATUS_NO_IMMEDIATE_DEADLINE: 0
        }

        vulnerable_count = 0
        for r in results:
            qc = r.get("quantum_class", QUANTUM_CLASS_UNKNOWN)
            st = r.get("status", STATUS_REQUIRES_REVIEW)
            class_breakdown[qc] = class_breakdown.get(qc, 0) + 1
            status_breakdown[st] = status_breakdown.get(st, 0) + 1

            if st in [STATUS_VULNERABLE_AT_HORIZON, STATUS_UNACCEPTABLE_AT_HORIZON]:
                vulnerable_count += 1

        return {
            "quantum_horizon": t_q,
            "target_horizon_year": CURRENT_YEAR + t_q,
            "total_components": len(results),
            "vulnerable_components": vulnerable_count,
            "class_breakdown": class_breakdown,
            "status_breakdown": status_breakdown,
            "components": results,
            "explanation": (
                f"Component-wise quantum exposure evaluated for {len(results)} cryptographic artifacts under "
                f"a conservative {t_q}-year CRQC threat scenario (~{CURRENT_YEAR + t_q}). "
                f"{vulnerable_count} components reach deadline or unacceptable strength at horizon."
            )
        }
