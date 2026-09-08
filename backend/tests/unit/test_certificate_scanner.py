import os
import tempfile
import datetime
import pytest
from app.scanners.certificate_scanner import CertificateScanner
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


def create_test_cert_pem(key_size=2048, hash_algo=None, self_signed=True, expired=False, san_domains=None):
    if not HAS_CRYPTOGRAPHY:
        return b"-----BEGIN CERTIFICATE-----\nMIIB...\n-----END CERTIFICATE-----"
    
    if hash_algo is None:
        hash_algo = hashes.SHA256()
        
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"test.sentriq.io")])
    issuer = subject if self_signed else x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"Sentriq Root CA")])
    
    now = datetime.datetime.now(datetime.timezone.utc)
    if expired:
        not_before = now - datetime.timedelta(days=365)
        not_after = now - datetime.timedelta(days=1)
    else:
        not_before = now - datetime.timedelta(days=1)
        not_after = now + datetime.timedelta(days=365)
        
    builder = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        not_before
    ).not_valid_after(
        not_after
    )
    
    if san_domains:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(domain) for domain in san_domains]),
            critical=False,
        )
        
    cert = builder.sign(key, hash_algo)
    from cryptography.hazmat.primitives import serialization
    return cert.public_bytes(serialization.Encoding.PEM)


@pytest.mark.skipif(not HAS_CRYPTOGRAPHY, reason="cryptography library required")
def test_certificate_scanner_valid_pem():
    scanner = CertificateScanner()
    pem_bytes = create_test_cert_pem(key_size=2048, self_signed=True, san_domains=[u"test.sentriq.io", u"api.sentriq.io"])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cert_path = os.path.join(tmpdir, "app.crt")
        with open(cert_path, "wb") as f:
            f.write(pem_bytes)
            
        findings = scanner.scan(tmpdir)
        assert len(findings) == 1
        finding = findings[0]
        
        assert finding.detector_name == "CertificateScanner"
        assert finding.asset_type == AssetType.CERTIFICATE
        assert finding.algorithm_name == "RSA-2048"
        assert finding.confidence == 1.0
        assert finding.extra_metadata["public_key_algorithm"] == "RSA"
        assert finding.extra_metadata["public_key_size"] == 2048
        assert finding.extra_metadata["is_self_signed"] is True
        assert finding.extra_metadata["is_expired"] is False
        assert finding.extra_metadata["is_weak"] is False
        assert "test.sentriq.io" in finding.extra_metadata["san"]
        assert "api.sentriq.io" in finding.extra_metadata["san"]


@pytest.mark.skipif(not HAS_CRYPTOGRAPHY, reason="cryptography library required")
def test_certificate_scanner_weak_and_expired():
    scanner = CertificateScanner()
    # Create a weak RSA-1024 cert with expired date
    pem_bytes = create_test_cert_pem(key_size=1024, self_signed=False, expired=True)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cert_path = os.path.join(tmpdir, "legacy.pem")
        with open(cert_path, "wb") as f:
            f.write(pem_bytes)
            
        findings = scanner.scan(tmpdir)
        assert len(findings) == 1
        finding = findings[0]
        
        assert finding.algorithm_name == "RSA-1024"
        assert finding.extra_metadata["is_weak"] is True
        assert finding.extra_metadata["is_expired"] is True
        assert finding.extra_metadata["is_self_signed"] is False
        reasons = finding.extra_metadata["weak_reasons"]
        assert any("1024" in r for r in reasons)
        assert any("expired" in r.lower() for r in reasons)


@pytest.mark.skipif(not HAS_CRYPTOGRAPHY, reason="cryptography library required")
def test_certificate_scanner_multi_cert_bundle():
    scanner = CertificateScanner()
    cert1 = create_test_cert_pem(key_size=2048)
    cert2 = create_test_cert_pem(key_size=4096)
    bundle_bytes = cert1 + b"\n" + cert2
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_path = os.path.join(tmpdir, "bundle.pem")
        with open(bundle_path, "wb") as f:
            f.write(bundle_bytes)
            
        findings = scanner.scan(tmpdir)
        assert len(findings) == 2
        algos = [f.algorithm_name for f in findings]
        assert "RSA-2048" in algos
        assert "RSA-4096" in algos


def test_certificate_scanner_corrupted_data():
    scanner = CertificateScanner()
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_path = os.path.join(tmpdir, "bad.crt")
        with open(bad_path, "wb") as f:
            f.write(b"NOT A REAL CERTIFICATE DATA")
            
        findings = scanner.scan(tmpdir)
        assert len(findings) == 1
        finding = findings[0]
        assert finding.algorithm_name == "UNKNOWN_CERT"
        assert finding.confidence == 0.5
        assert finding.extra_metadata["is_weak"] is True
