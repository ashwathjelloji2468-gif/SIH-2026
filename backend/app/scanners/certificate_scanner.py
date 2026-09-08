import os
import re
import datetime
from typing import List, Dict, Any, Optional

from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

# Optional import of cryptography – fallback if unavailable
try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa, ed25519, ed448
    HAS_CRYPTOGRAPHY = True
except ImportError:  # pragma: no cover
    x509 = None
    default_backend = None
    hashes = None
    HAS_CRYPTOGRAPHY = False


WEAK_HASH_ALGORITHMS = {"sha1", "md5", "md2", "md4", "sha-1"}


class CertificateScanner(BaseScanner):
    """Parse X.509 certificates (PEM or DER) and extract detailed cryptographic metadata.

    Supports .crt, .cer, and .pem files (including multi-certificate PEM bundles).
    Detects signature algorithms, public key types/sizes, self-signed certificates,
    expiration status, Subject Alternative Names (SAN), and flags weak/legacy parameters.
    """

    def _parse_with_cryptography(self, cert: Any, path: str) -> RawFinding:
        """Extract rich cryptographic findings from an x509.Certificate object."""
        # 1. Subject and Issuer
        subject_str = cert.subject.rfc4514_string()
        issuer_str = cert.issuer.rfc4514_string()
        is_self_signed = (cert.subject == cert.issuer)

        # 2. Expiration and Validity Dates
        now = datetime.datetime.now(datetime.timezone.utc)
        try:
            not_before = cert.not_valid_before_utc
            not_after = cert.not_valid_after_utc
        except AttributeError:
            not_before = cert.not_valid_before.replace(tzinfo=datetime.timezone.utc)
            not_after = cert.not_valid_after.replace(tzinfo=datetime.timezone.utc)

        is_expired = now > not_after
        days_until_expiration = (not_after - now).days

        # 3. Public Key Algorithm & Key Size
        pub_key = cert.public_key()
        key_algo = pub_key.__class__.__name__
        key_size = getattr(pub_key, "key_size", None)

        if isinstance(pub_key, rsa.RSAPublicKey):
            key_algo_name = "RSA"
        elif isinstance(pub_key, ec.EllipticCurvePublicKey):
            curve_name = getattr(pub_key.curve, "name", "unknown")
            key_algo_name = f"ECDSA-{curve_name}"
        elif isinstance(pub_key, dsa.DSAPublicKey):
            key_algo_name = "DSA"
        elif isinstance(pub_key, ed25519.Ed25519PublicKey):
            key_algo_name = "Ed25519"
            key_size = 256
        elif isinstance(pub_key, ed448.Ed448PublicKey):
            key_algo_name = "Ed448"
            key_size = 448
        else:
            key_algo_name = key_algo.replace("_RSAPublicKey", "RSA").replace("_EllipticCurvePublicKey", "ECDSA")

        # Formulate canonical algorithm name for RawFinding
        if key_size and key_algo_name in ("RSA", "DSA"):
            algorithm_name = f"{key_algo_name}-{key_size}"
        else:
            algorithm_name = key_algo_name

        # 4. Signature Algorithm & Hash
        sig_algo_name = None
        try:
            if hasattr(cert, "signature_algorithm_oid"):
                sig_algo_name = cert.signature_algorithm_oid._name
                if sig_algo_name == "Unknown OID":
                    sig_algo_name = cert.signature_algorithm_oid.dotted_string
        except Exception:
            pass

        sig_hash_name = None
        try:
            if cert.signature_hash_algorithm:
                sig_hash_name = cert.signature_hash_algorithm.name.lower()
        except Exception:
            pass

        if not sig_algo_name or sig_algo_name == "Unknown OID":
            sig_algo_name = f"{sig_hash_name or 'unknown'}-with-{key_algo_name}"

        # 5. SAN (Subject Alternative Names)
        san_list = []
        try:
            ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            san_list = [str(name) for name in ext.value.get_values_for_type(x509.DNSName)]
            ip_names = [str(ip) for ip in ext.value.get_values_for_type(x509.IPAddress)]
            san_list.extend(ip_names)
        except Exception:
            pass

        # 6. Fingerprint
        fingerprint_sha256 = None
        try:
            fingerprint_sha256 = cert.fingerprint(hashes.SHA256()).hex()
        except Exception:
            pass

        # 7. Weak / Legacy / Security Risk Analysis
        weak_reasons = []

        # Check RSA key size
        if key_algo_name == "RSA" and key_size and key_size < 2048:
            weak_reasons.append(f"Weak RSA key size ({key_size} bits < 2048)")

        # Check ECC key size
        if "ECDSA" in key_algo_name and key_size and key_size < 224:
            weak_reasons.append(f"Weak ECC key size ({key_size} bits < 224)")

        # Check Signature Hash Algorithm
        sig_algo_lower = sig_algo_name.lower() if sig_algo_name else ""
        if sig_hash_name in WEAK_HASH_ALGORITHMS or any(w in sig_algo_lower for w in ["sha1", "md5", "md2", "md4"]):
            weak_reasons.append(f"Weak/deprecated signature algorithm ({sig_algo_name})")

        # Check Expiration
        if is_expired:
            weak_reasons.append(f"Certificate expired on {not_after.strftime('%Y-%m-%d')}")

        is_weak = len(weak_reasons) > 0

        # Construct finding metadata
        extra_metadata: Dict[str, Any] = {
            "subject": subject_str,
            "issuer": issuer_str,
            "serial_number": hex(cert.serial_number),
            "not_before": not_before.isoformat(),
            "not_after": not_after.isoformat(),
            "public_key_algorithm": key_algo_name,
            "public_key_size": key_size,
            "signature_algorithm": sig_algo_name,
            "signature_hash_algorithm": sig_hash_name,
            "san": san_list,
            "is_self_signed": is_self_signed,
            "is_expired": is_expired,
            "days_until_expiration": days_until_expiration,
            "is_weak": is_weak,
            "weak_reasons": weak_reasons,
            "fingerprint_sha256": fingerprint_sha256,
            "file_path": path,
        }

        context = f"X.509 Cert [{subject_str or 'No CN'}] Alg: {algorithm_name}, Sig: {sig_algo_name}"
        if is_self_signed:
            context += " (Self-Signed)"
        if is_expired:
            context += " (EXPIRED)"

        return RawFinding(
            detector_name="CertificateScanner",
            target_path=path,
            file_path=path,
            line_number=1,
            asset_type=AssetType.CERTIFICATE,
            algorithm_name=algorithm_name,
            purpose=CryptoPurpose.AUTHENTICATION,
            matched_text="certificate",
            context=context,
            confidence=1.0,
            evidence_type=EvidenceType.OBSERVED,
            extra_metadata=extra_metadata,
        )

    def _parse_certificate(self, data: bytes, path: str) -> List[RawFinding]:
        """Parse a single certificate blob (PEM or DER) and return findings."""
        if not HAS_CRYPTOGRAPHY:
            return self._fallback_parse(data, path, error_msg="cryptography library missing")

        try:
            cert = x509.load_pem_x509_certificate(data, default_backend())
            return [self._parse_with_cryptography(cert, path)]
        except Exception:
            try:
                cert = x509.load_der_x509_certificate(data, default_backend())
                return [self._parse_with_cryptography(cert, path)]
            except Exception as e:
                return self._fallback_parse(data, path, error_msg=str(e))

    def _fallback_parse(self, data: bytes, path: str, error_msg: str) -> List[RawFinding]:
        """Fallback certificate scanner when cryptography library is missing or fails."""
        text = data.decode("utf-8", errors="ignore")
        has_pem_header = "-----BEGIN CERTIFICATE-----" in text

        extra_md: Dict[str, Any] = {
            "error": error_msg,
            "raw_cert_detected": has_pem_header,
            "file_path": path,
            "is_weak": True,
            "weak_reasons": ["Unparsed certificate file"],
        }

        confidence = 0.7 if has_pem_header else 0.5
        algo_name = "X509-CERT" if has_pem_header else "UNKNOWN_CERT"

        return [RawFinding(
            detector_name="CertificateScanner",
            target_path=path,
            file_path=path,
            line_number=1,
            asset_type=AssetType.CERTIFICATE,
            algorithm_name=algo_name,
            purpose=CryptoPurpose.AUTHENTICATION,
            matched_text="certificate",
            context=f"Certificate raw scan: {error_msg}",
            confidence=confidence,
            evidence_type=EvidenceType.OBSERVED if has_pem_header else EvidenceType.UNKNOWN,
            extra_metadata=extra_md,
        )]

    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        if not os.path.isdir(target_path):
            return findings

        valid_exts = (".crt", ".cer", ".pem")

        for root, _, files in os.walk(target_path):
            for file in files:
                if not file.lower().endswith(valid_exts):
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, target_path)

                try:
                    with open(full_path, "rb") as f:
                        data = f.read()
                except Exception:
                    continue

                # Handle multi-cert PEM files
                file_findings = []
                if b"-----BEGIN CERTIFICATE-----" in data:
                    parts = data.split(b"-----END CERTIFICATE-----")
                    for part in parts:
                        if b"-----BEGIN CERTIFICATE-----" not in part:
                            continue
                        pem = part + b"-----END CERTIFICATE-----\n"
                        file_findings.extend(self._parse_certificate(pem, rel_path))
                else:
                    file_findings.extend(self._parse_certificate(data, rel_path))

                # Detect cross-component references to this certificate file across codebase
                refs = self._find_cert_references(target_path, rel_path)
                for f_item in file_findings:
                    f_item.extra_metadata["references"] = refs
                    f_item.extra_metadata["cryptoRefArray"] = refs

                findings.extend(file_findings)

        return findings

    def _find_cert_references(self, target_path: str, cert_rel_path: str) -> List[str]:
        refs = []
        base_name = os.path.basename(cert_rel_path)
        if not os.path.isdir(target_path):
            return refs
        for root, _, files in os.walk(target_path):
            for f in files:
                if f.endswith((".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".json", ".yaml", ".yml")):
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, target_path)
                    if rel_path == cert_rel_path:
                        continue
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                            content = file_obj.read()
                            if base_name in content or cert_rel_path in content:
                                refs.append(rel_path)
                    except Exception:
                        pass
        return list(set(refs))

