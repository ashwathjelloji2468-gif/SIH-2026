import os
from typing import List
from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

# Optional import of cryptography – fallback if unavailable
try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
except ImportError:  # pragma: no cover
    x509 = None
    default_backend = None

class CertificateScanner(BaseScanner):
    """Parse X.509 certificates and extract detailed metadata.

    Supports .crt, .cer (DER or PEM) and .pem files. Handles PEM files that
    contain multiple concatenated certificates.
    """

    def _parse_certificate(self, data: bytes, path: str) -> List[RawFinding]:
        """Parse a single certificate blob (PEM or DER) and return findings.

        Returns a list – normally a single element, but kept as a list to
        simplify handling of multi‑cert PEM files where the caller will invoke
        this for each cert.
        """
        if x509 is None:
            # Cryptography library missing – produce an UNKNOWN finding
            return [RawFinding(
                detector_name="CertificateScanner",
                target_path=path,
                file_path=path,
                line_number=1,
                asset_type=AssetType.CERTIFICATE,
                algorithm_name="UNKNOWN_CERT",
                purpose=CryptoPurpose.UNKNOWN,
                matched_text="",
                context="cryptography library not available",
                confidence=0.5,
                evidence_type=EvidenceType.UNKNOWN,
                extra_metadata={"error": "cryptography library missing"},
            )]
        try:
            # Try PEM first
            cert = x509.load_pem_x509_certificate(data, default_backend())
        except Exception:
            try:
                cert = x509.load_der_x509_certificate(data, default_backend())
            except Exception as e:
                # Parsing failed – return UNKNOWN finding
                return [RawFinding(
                    detector_name="CertificateScanner",
                    target_path=path,
                    file_path=path,
                    line_number=1,
                    asset_type=AssetType.CERTIFICATE,
                    algorithm_name="UNKNOWN_CERT",
                    purpose=CryptoPurpose.UNKNOWN,
                    matched_text="",
                    context=f"Failed to parse certificate: {e}",
                    confidence=0.5,
                    evidence_type=EvidenceType.UNKNOWN,
                    extra_metadata={"error": str(e)},
                )]
        # Extract fields
        san = []
        try:
            ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            san = list(ext.value.get_values_for_type(x509.DNSName))
        except Exception:
            pass
        public_key = cert.public_key()
        key_algo = public_key.__class__.__name__
        key_size = getattr(public_key, "key_size", None)
        signature_algo = cert.signature_hash_algorithm.name if cert.signature_hash_algorithm else None
        is_expired = cert.not_valid_after < cert.not_valid_before
        return [RawFinding(
            detector_name="CertificateScanner",
            target_path=path,
            file_path=path,
            line_number=1,
            asset_type=AssetType.CERTIFICATE,
            algorithm_name=key_algo,
            purpose=CryptoPurpose.AUTHENTICATION,
            matched_text="certificate",
            context="X.509 certificate parsed",
            confidence=1.0,
            evidence_type=EvidenceType.OBSERVED,
            extra_metadata={
                "subject": cert.subject.rfc4514_string(),
                "issuer": cert.issuer.rfc4514_string(),
                "serial_number": cert.serial_number,
                "not_before": cert.not_valid_before.isoformat(),
                "not_after": cert.not_valid_after.isoformat(),
                "public_key_algorithm": key_algo,
                "public_key_size": key_size,
                "signature_algorithm": signature_algo,
                "san": san,
                "file_path": path,
                "is_expired": is_expired,
            },
        )]

    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        if not os.path.isdir(target_path):
            return findings
        for root, _, files in os.walk(target_path):
            for file in files:
                if not file.lower().endswith((".crt", ".cer", ".pem")):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, target_path)
                try:
                    with open(full_path, "rb") as f:
                        data = f.read()
                except Exception:
                    continue
                if file.lower().endswith('.pem'):
                    # Split possible multiple PEM certificates
                    parts = data.split(b"-----END CERTIFICATE-----")
                    for part in parts:
                        if b"-----BEGIN CERTIFICATE-----" not in part:
                            continue
                        pem = part + b"-----END CERTIFICATE-----\n"
                        findings.extend(self._parse_certificate(pem, rel_path))
                else:
                    findings.extend(self._parse_certificate(data, rel_path))
        return findings
