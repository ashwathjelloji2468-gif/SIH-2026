import os
import subprocess
import re
from typing import List, Dict, Tuple, Optional, Any
from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

class BinaryScanner(BaseScanner):
    """Scans compiled binaries (.so, .dll, .dylib, .exe, .a, .o, .bin) for embedded
    cryptographic identifiers, algorithm specifications, cipher modes, and crypto libraries.

    Uses system `strings` utility (with pure Python binary regex fallback) to extract
    printable strings from binaries, applies precise pattern matching, extracts key sizes
    and modes, and constructs rich RawFinding objects with confidence scoring.
    """

    BINARY_EXTS = (".so", ".dll", ".dylib", ".exe", ".a", ".o", ".bin")

    # High-precision regular expressions for crypto identification in binary strings
    PATTERNS: List[Dict[str, Any]] = [
        # --- Cryptographic Libraries ---
        {
            "regex": re.compile(r"\bOpenSSL\s+([0-9]+\.[0-9]+\.[0-9]+[a-z]?)\b", re.IGNORECASE),
            "alg": "OpenSSL",
            "purpose": CryptoPurpose.UNKNOWN,
            "asset_type": AssetType.DEPENDENCY,
            "confidence": 0.95,
            "library": "OpenSSL",
            "extract_version": True,
        },
        {
            "regex": re.compile(r"\b(BoringSSL|LibreSSL|wolfSSL|mbedTLS|PolarSSL|libsodium|Botan|Crypto\+\+|GnuTLS|NSS)\b", re.IGNORECASE),
            "alg": "CRYPTO_LIBRARY",
            "purpose": CryptoPurpose.UNKNOWN,
            "asset_type": AssetType.DEPENDENCY,
            "confidence": 0.90,
            "extract_library": True,
        },

        # --- Post-Quantum Candidates (NIST PQC) ---
        {
            "regex": re.compile(r"\b(ML-KEM-(?:512|768|1024)|Kyber(?:512|768|1024))\b", re.IGNORECASE),
            "alg": "ML-KEM",
            "purpose": CryptoPurpose.KEY_ESTABLISHMENT,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.95,
        },
        {
            "regex": re.compile(r"\b(ML-DSA-(?:44|65|87)|Dilithium(?:2|3|5))\b", re.IGNORECASE),
            "alg": "ML-DSA",
            "purpose": CryptoPurpose.SIGNATURE,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.95,
        },
        {
            "regex": re.compile(r"\b(SLH-DSA|SPHINCS\+)\b", re.IGNORECASE),
            "alg": "SLH-DSA",
            "purpose": CryptoPurpose.SIGNATURE,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.95,
        },

        # --- AES & Symmetric Ciphers ---
        {
            "regex": re.compile(r"\bAES[_-]?(128|192|256)[_-]?(GCM|CBC|CTR|ECB|CFB|OFB|CCM|XTS)", re.IGNORECASE),
            "alg": "AES",
            "purpose": CryptoPurpose.ENCRYPTION,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.95,
            "has_keysize_group": 1,
            "has_mode_group": 2,
        },
        {
            "regex": re.compile(r"\bEVP_aes_(128|192|256)_(gcm|cbc|ctr|ecb|cfb|ofb)", re.IGNORECASE),
            "alg": "AES",
            "purpose": CryptoPurpose.ENCRYPTION,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.95,
            "has_keysize_group": 1,
            "has_mode_group": 2,
            "library": "OpenSSL",
        },
        {
            "regex": re.compile(r"\bAES[_-]?(128|192|256)", re.IGNORECASE),
            "alg": "AES",
            "purpose": CryptoPurpose.ENCRYPTION,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.90,
            "has_keysize_group": 1,
        },
        {
            "regex": re.compile(r"\bAES[_-]?(GCM|CBC|CTR|ECB|CFB|OFB)", re.IGNORECASE),
            "alg": "AES",
            "purpose": CryptoPurpose.ENCRYPTION,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.85,
            "has_mode_group": 1,
        },
        {
            "regex": re.compile(r"\b(AES_encrypt|AES_decrypt|AES_set_encrypt_key|AES_cbc_encrypt)\b", re.IGNORECASE),
            "alg": "AES",
            "purpose": CryptoPurpose.ENCRYPTION,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.90,
        },

        # --- RSA & Asymmetric Ciphers ---
        {
            "regex": re.compile(r"\bRSA[_-]?(1024|2048|3072|4096|8192)", re.IGNORECASE),
            "alg": "RSA",
            "purpose": CryptoPurpose.SIGNATURE,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.95,
            "has_keysize_group": 1,
        },
        {
            "regex": re.compile(r"\b(RSA_generate_key|RSA_private_encrypt|RSA_public_decrypt|RSA_sign|RSA_verify|EVP_PKEY_RSA|PEM_read_RSAPrivateKey)\b", re.IGNORECASE),
            "alg": "RSA",
            "purpose": CryptoPurpose.SIGNATURE,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.90,
        },

        # --- Elliptic Curve Cryptography (ECC / EdDSA / ECDH) ---
        {
            "regex": re.compile(r"\b(ECDSA[_-]?(?:P|SHA)?(?:256|384|521)?)", re.IGNORECASE),
            "alg": "ECDSA",
            "purpose": CryptoPurpose.SIGNATURE,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.95,
        },
        {
            "regex": re.compile(r"\b(Ed25519|Ed448|EdDSA)\b", re.IGNORECASE),
            "alg": "Ed25519",
            "purpose": CryptoPurpose.SIGNATURE,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.95,
        },
        {
            "regex": re.compile(r"\b(ECDH[_-]?(?:P)?(?:256|384|521)?|X25519|X448|Curve25519)\b", re.IGNORECASE),
            "alg": "ECDH",
            "purpose": CryptoPurpose.KEY_ESTABLISHMENT,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.95,
        },
        {
            "regex": re.compile(r"\b(secp256k1|secp256r1|secp384r1|prime256v1|NIST[_-]?P[_-]?(?:256|384|521))\b", re.IGNORECASE),
            "alg": "ECDSA",
            "purpose": CryptoPurpose.SIGNATURE,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.90,
        },

        # --- ChaCha20 / Poly1305 ---
        {
            "regex": re.compile(r"\bChaCha20[_-]?Poly1305", re.IGNORECASE),
            "alg": "ChaCha20-Poly1305",
            "purpose": CryptoPurpose.ENCRYPTION,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.95,
            "default_keysize": 256,
        },
        {
            "regex": re.compile(r"\bChaCha20", re.IGNORECASE),
            "alg": "ChaCha20",
            "purpose": CryptoPurpose.ENCRYPTION,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.90,
            "default_keysize": 256,
        },

        # --- Hashes & MACs ---
        {
            "regex": re.compile(r"\b(SHA[_-]?256|SHA256)", re.IGNORECASE),
            "alg": "SHA-256",
            "purpose": CryptoPurpose.HASHING,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.90,
            "default_keysize": 256,
        },
        {
            "regex": re.compile(r"\b(SHA[_-]?384|SHA384)", re.IGNORECASE),
            "alg": "SHA-384",
            "purpose": CryptoPurpose.HASHING,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.90,
            "default_keysize": 384,
        },
        {
            "regex": re.compile(r"\b(SHA[_-]?512|SHA512)", re.IGNORECASE),
            "alg": "SHA-512",
            "purpose": CryptoPurpose.HASHING,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.90,
            "default_keysize": 512,
        },
        {
            "regex": re.compile(r"\b(SHA[_-]?1|SHA1)", re.IGNORECASE),
            "alg": "SHA-1",
            "purpose": CryptoPurpose.HASHING,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.85,
            "default_keysize": 160,
        },
        {
            "regex": re.compile(r"\b(MD5|MD5_Init)", re.IGNORECASE),
            "alg": "MD5",
            "purpose": CryptoPurpose.HASHING,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.80,
            "default_keysize": 128,
        },
        {
            "regex": re.compile(r"\bHMAC[_-]?(SHA256|SHA384|SHA512|SHA1|MD5)?\b", re.IGNORECASE),
            "alg": "HMAC",
            "purpose": CryptoPurpose.MAC,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.90,
        },

        # --- Legacy Symmetric ---
        {
            "regex": re.compile(r"\b(3DES|TripleDES|DES-EDE3|DES_ede3_cbc)\b", re.IGNORECASE),
            "alg": "3DES",
            "purpose": CryptoPurpose.ENCRYPTION,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.90,
            "default_keysize": 168,
        },
        {
            "regex": re.compile(r"\bDES[_-]?(GCM|CBC|ECB)\b", re.IGNORECASE),
            "alg": "DES",
            "purpose": CryptoPurpose.ENCRYPTION,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.85,
            "default_keysize": 56,
            "has_mode_group": 1,
        },
        {
            "regex": re.compile(r"\b(RC4|ARC4)\b", re.IGNORECASE),
            "alg": "RC4",
            "purpose": CryptoPurpose.ENCRYPTION,
            "asset_type": AssetType.ALGORITHM,
            "confidence": 0.80,
        },
    ]

    def _extract_strings(self, file_path: str) -> List[str]:
        """Extract printable ASCII & UTF-8 strings from binary using `strings` command,
        falling back to pure Python parsing if `strings` binary is unavailable or fails.
        """
        try:
            result = subprocess.run(
                ["strings", file_path],
                capture_output=True,
                text=True,
                timeout=10,
                errors="ignore"
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.splitlines()
        except Exception:
            pass

        # Pure Python fallback if system `strings` fails or is missing
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            ascii_strings = re.findall(b"[A-Za-z0-9_\\-\\.:\\/\\s]{4,}", content)
            return [s.decode("ascii", errors="ignore").strip() for s in ascii_strings if s.strip()]
        except Exception:
            return []

    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        if not os.path.exists(target_path):
            return findings

        # Single file target or directory walk
        target_files: List[Tuple[str, str]] = []
        if os.path.isfile(target_path):
            if target_path.endswith(self.BINARY_EXTS):
                target_files.append((target_path, os.path.basename(target_path)))
        else:
            for root, _, files in os.walk(target_path):
                for file in files:
                    if file.endswith(self.BINARY_EXTS):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, target_path)
                        target_files.append((full_path, rel_path))

        for full_path, rel_path in target_files:
            file_strings = self._extract_strings(full_path)
            if not file_strings:
                continue

            # Deduplicate matches per binary file to prevent spamming findings
            # Key: (alg_name, purpose, key_size, mode, library, matched_text)
            grouped_matches: Dict[Tuple[str, CryptoPurpose, Optional[int], Optional[str], Optional[str], str], Dict[str, Any]] = {}

            for line in file_strings:
                line_str = line.strip()
                if not line_str or len(line_str) < 3:
                    continue

                for pattern_info in self.PATTERNS:
                    match = pattern_info["regex"].search(line_str)
                    if match:
                        alg_name = pattern_info["alg"]
                        purpose = pattern_info["purpose"]
                        asset_type = pattern_info["asset_type"]
                        confidence = pattern_info["confidence"]
                        library = pattern_info.get("library")
                        key_size = pattern_info.get("default_keysize")
                        mode = None

                        if pattern_info.get("extract_library"):
                            library = match.group(1)
                            alg_name = f"{library} (Library)"
                        elif pattern_info.get("extract_version"):
                            ver = match.group(1)
                            alg_name = f"OpenSSL-{ver}"
                            library = "OpenSSL"

                        if pattern_info.get("has_keysize_group"):
                            try:
                                key_size = int(match.group(pattern_info["has_keysize_group"]))
                            except (ValueError, IndexError):
                                pass

                        if pattern_info.get("has_mode_group"):
                            try:
                                mode = match.group(pattern_info["has_mode_group"]).upper()
                            except (ValueError, IndexError):
                                pass

                        # Additional mode discovery from the matching string
                        if not mode:
                            mode_match = re.search(r"\b(GCM|CBC|CTR|ECB|CFB|OFB|CCM|XTS)\b", line_str, re.IGNORECASE)
                            if mode_match:
                                mode = mode_match.group(1).upper()

                        # Additional key size discovery from matching string
                        if not key_size:
                            ks_match = re.search(r"\b(128|192|256|512|1024|2048|3072|4096|8192)\b", line_str)
                            if ks_match:
                                try:
                                    key_size = int(ks_match.group(1))
                                except ValueError:
                                    pass

                        matched_text = match.group(0)
                        group_key = (alg_name, purpose, key_size, mode, library, matched_text)

                        if group_key not in grouped_matches:
                            grouped_matches[group_key] = {
                                "asset_type": asset_type,
                                "confidence": confidence,
                                "occurrences": 1,
                                "matched_line": line_str,
                            }
                        else:
                            grouped_matches[group_key]["occurrences"] += 1

                        break  # Most specific pattern matched for this string line

            # Convert grouped matches into RawFinding objects
            ext = os.path.splitext(rel_path)[1].lower()
            for (alg_name, purpose, key_size, mode, library, matched_text), meta in grouped_matches.items():
                extra_meta = {
                    "algorithm": alg_name,
                    "possible_key_size": key_size,
                    "mode": mode,
                    "library": library,
                    "matched_string": matched_text,
                    "occurrences": meta["occurrences"],
                    "binary_file_extension": ext,
                }

                context_str = f"Binary match '{matched_text}' in {rel_path}"
                if key_size:
                    context_str += f" (key size: {key_size}-bit)"
                if mode:
                    context_str += f" (mode: {mode})"
                if library:
                    context_str += f" [Library: {library}]"
                if meta["occurrences"] > 1:
                    context_str += f" - {meta['occurrences']} occurrences"

                findings.append(RawFinding(
                    detector_name="BinaryScanner",
                    target_path=target_path,
                    file_path=rel_path,
                    line_number=None,
                    asset_type=meta["asset_type"],
                    algorithm_name=alg_name,
                    purpose=purpose,
                    matched_text=meta["matched_line"],
                    context=context_str,
                    confidence=meta["confidence"],
                    evidence_type=EvidenceType.OBSERVED,
                    key_size=key_size,
                    extra_metadata=extra_meta,
                ))

        return findings
