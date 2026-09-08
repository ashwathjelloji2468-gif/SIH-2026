import os
import tempfile
import pytest
from app.scanners.container_scanner import ContainerScanner
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

def test_container_scanner_dockerfile_parsing_and_versions():
    scanner = ContainerScanner()

    dockerfile_content = """
    # Sample Dockerfile for testing
    FROM python:3.11-alpine as builder
    
    RUN apk add --no-cache openssl=3.1.2-r0 libcrypto3 ca-certificates
    RUN pip install pycryptodome==3.18.0 cryptography>=41.0.0 liboqs
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        df_path = os.path.join(tmpdir, "Dockerfile")
        with open(df_path, "w", encoding="utf-8") as f:
            f.write(dockerfile_content)

        findings = scanner.scan(tmpdir)

        assert len(findings) >= 5
        names = [f.algorithm_name for f in findings]
        assert "python:3.11-alpine" in names
        assert "openssl" in names
        assert "pycryptodome" in names
        assert "cryptography" in names
        assert "liboqs" in names

        # Test base image finding
        base_finding = next(f for f in findings if f.algorithm_name == "python:3.11-alpine")
        assert base_finding.extra_metadata["type"] == "base_image"
        assert base_finding.extra_metadata["image_tag"] == "3.11-alpine"
        assert base_finding.asset_type == AssetType.CONTAINER

        # Test versioned package finding
        openssl_finding = next(f for f in findings if f.algorithm_name == "openssl")
        assert openssl_finding.extra_metadata["version"] == "3.1.2-r0"
        assert openssl_finding.confidence == 0.95
        assert openssl_finding.extra_metadata["package_manager"] == "apk"

        # Test PQC package finding
        pqc_finding = next(f for f in findings if f.algorithm_name == "liboqs")
        assert pqc_finding.purpose == CryptoPurpose.KEY_ESTABLISHMENT
        assert pqc_finding.extra_metadata["category"] == "pqc_library"

def test_container_scanner_multiple_dockerfiles():
    scanner = ContainerScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        df1 = os.path.join(tmpdir, "Dockerfile")
        df2 = os.path.join(tmpdir, "Dockerfile.prod")

        with open(df1, "w") as f:
            f.write("FROM ubuntu:22.04\nRUN apt-get install -y libssl-dev=1.1.1f-1ubuntu2\n")
        with open(df2, "w") as f:
            f.write("FROM alpine:3.18\nRUN apk add wolfssl-dev\n")

        findings = scanner.scan(tmpdir)

        names = [f.algorithm_name for f in findings]
        assert "ubuntu:22.04" in names
        assert "alpine:3.18" in names
        assert "libssl-dev" in names
        assert "wolfssl-dev" in names or "wolfssl" in names
