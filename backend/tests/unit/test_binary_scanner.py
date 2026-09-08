import os
import tempfile
import pytest
from app.scanners.binary_scanner import BinaryScanner
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

def test_binary_scanner_pattern_matching_and_metadata():
    scanner = BinaryScanner()

    # Create a temporary directory containing mock binary files
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_binary_path = os.path.join(tmpdir, "libcrypto_test.so")
        with open(fake_binary_path, "wb") as f:
            f.write(b"\x7fELF\x02\x01\x01\x00")
            f.write(b"\x00" * 16)
            f.write(b"OpenSSL 3.0.2 15 Mar 2022\n")
            f.write(b"EVP_aes_256_gcm\n")
            f.write(b"RSA_2048_key_gen\n")
            f.write(b"ECDSA_P256_sign\n")
            f.write(b"ChaCha20_Poly1305_encrypt\n")
            f.write(b"ML-KEM-768\n")

        findings = scanner.scan(tmpdir)

        assert len(findings) >= 5
        algs = [f.algorithm_name for f in findings]
        assert "OpenSSL-3.0.2" in algs or "OpenSSL" in [f.extra_metadata.get("library") for f in findings]
        assert "AES" in algs
        assert "RSA" in algs
        assert "ECDSA" in algs
        assert "ML-KEM" in algs

        # Verify extra_metadata fields
        aes_finding = next(f for f in findings if f.algorithm_name == "AES")
        assert aes_finding.extra_metadata["possible_key_size"] == 256
        assert aes_finding.extra_metadata["mode"] == "GCM"
        assert aes_finding.extra_metadata["library"] == "OpenSSL"
        assert aes_finding.confidence >= 0.90
        assert aes_finding.detector_name == "BinaryScanner"
        assert aes_finding.evidence_type == EvidenceType.OBSERVED

        # Verify RSA finding
        rsa_finding = next(f for f in findings if f.algorithm_name == "RSA")
        assert rsa_finding.extra_metadata["possible_key_size"] == 2048
        assert rsa_finding.purpose == CryptoPurpose.SIGNATURE

        # Verify ML-KEM finding
        pqc_finding = next(f for f in findings if f.algorithm_name == "ML-KEM")
        assert pqc_finding.purpose == CryptoPurpose.KEY_ESTABLISHMENT
        assert pqc_finding.confidence == 0.95

def test_binary_scanner_supported_extensions():
    scanner = BinaryScanner()
    assert ".so" in scanner.BINARY_EXTS
    assert ".dll" in scanner.BINARY_EXTS
    assert ".dylib" in scanner.BINARY_EXTS
    assert ".exe" in scanner.BINARY_EXTS
    assert ".a" in scanner.BINARY_EXTS
    assert ".o" in scanner.BINARY_EXTS
    assert ".bin" in scanner.BINARY_EXTS
