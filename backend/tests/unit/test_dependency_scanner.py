import os
import tempfile
import pytest
from app.scanners.dependency_scanner import DependencyScanner
from app.models.enums import AssetType, CryptoPurpose


def test_dependency_scanner_requirements_txt():
    scanner = DependencyScanner()
    req_content = """
# Python requirements
cryptography>=41.0.0
pycryptodome==3.18.0
requests==2.31.0
bcrypt==4.0.1
pqcrypto==0.2.1
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        req_path = os.path.join(tmpdir, "requirements.txt")
        with open(req_path, "w", encoding="utf-8") as f:
            f.write(req_content)

        findings = scanner.scan(tmpdir)
        pkgs = {f.extra_metadata["package"]: f for f in findings}

        assert "cryptography" in pkgs
        assert pkgs["cryptography"].extra_metadata["version"] == "41.0.0"
        assert pkgs["cryptography"].asset_type == AssetType.DEPENDENCY
        assert pkgs["cryptography"].confidence == 1.0

        assert "pycryptodome" in pkgs
        assert pkgs["pycryptodome"].extra_metadata["version"] == "3.18.0"

        assert "bcrypt" in pkgs
        assert pkgs["bcrypt"].extra_metadata["category"] == "hashing"

        assert "pqcrypto" in pkgs
        assert pkgs["pqcrypto"].extra_metadata["is_pqc"] is True
        assert pkgs["pqcrypto"].extra_metadata["category"] == "pqc"

        # Non-crypto dependency requests should not be flagged
        assert "requests" not in pkgs


def test_dependency_scanner_package_json():
    scanner = DependencyScanner()
    pkg_json_content = """
{
  "name": "test-app",
  "dependencies": {
    "express": "^4.18.2",
    "crypto-js": "^4.1.1",
    "jose": "^4.14.4",
    "libsodium-wrappers": "0.7.11"
  },
  "devDependencies": {
    "bcrypt": "^5.1.0"
  }
}
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = os.path.join(tmpdir, "package.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(pkg_json_content)

        findings = scanner.scan(tmpdir)
        pkgs = {f.extra_metadata["package"]: f for f in findings}

        assert "crypto-js" in pkgs
        assert pkgs["crypto-js"].extra_metadata["version"] == "4.1.1"
        assert pkgs["crypto-js"].extra_metadata["ecosystem"] == "npm"

        assert "jose" in pkgs
        assert pkgs["jose"].extra_metadata["category"] == "jwt_tokens"

        assert "libsodium-wrappers" in pkgs
        assert pkgs["libsodium-wrappers"].extra_metadata["version"] == "0.7.11"

        assert "express" not in pkgs


def test_dependency_scanner_maven_pom():
    scanner = DependencyScanner()
    pom_content = """<project>
  <dependencies>
    <dependency>
      <groupId>org.bouncycastle</groupId>
      <artifactId>bcprov-jdk18on</artifactId>
      <version>1.76</version>
    </dependency>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>32.1.2-jre</version>
    </dependency>
  </dependencies>
</project>"""

    with tempfile.TemporaryDirectory() as tmpdir:
        pom_path = os.path.join(tmpdir, "pom.xml")
        with open(pom_path, "w", encoding="utf-8") as f:
            f.write(pom_content)

        findings = scanner.scan(tmpdir)
        pkgs = {f.extra_metadata["package"]: f for f in findings}

        assert "org.bouncycastle:bcprov-jdk18on" in pkgs
        assert pkgs["org.bouncycastle:bcprov-jdk18on"].extra_metadata["version"] == "1.76"
        assert pkgs["org.bouncycastle:bcprov-jdk18on"].extra_metadata["ecosystem"] == "maven"
        assert "com.google.guava:guava" not in pkgs


def test_dependency_scanner_go_mod():
    scanner = DependencyScanner()
    go_mod_content = """module main

go 1.21

require (
	golang.org/x/crypto v0.14.0
	github.com/gin-gonic/gin v1.9.1
)
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        go_path = os.path.join(tmpdir, "go.mod")
        with open(go_path, "w", encoding="utf-8") as f:
            f.write(go_mod_content)

        findings = scanner.scan(tmpdir)
        pkgs = {f.extra_metadata["package"]: f for f in findings}

        assert "golang.org/x/crypto" in pkgs
        assert pkgs["golang.org/x/crypto"].extra_metadata["version"] == "0.14.0"
        assert pkgs["golang.org/x/crypto"].extra_metadata["ecosystem"] == "go"
        assert "github.com/gin-gonic/gin" not in pkgs


def test_dependency_scanner_cargo_toml():
    scanner = DependencyScanner()
    cargo_content = """[package]
name = "crypto-app"
version = "0.1.0"

[dependencies]
ring = "0.17.5"
rustls = "0.21.7"
tokio = "1.32.0"
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cargo_path = os.path.join(tmpdir, "Cargo.toml")
        with open(cargo_path, "w", encoding="utf-8") as f:
            f.write(cargo_content)

        findings = scanner.scan(tmpdir)
        pkgs = {f.extra_metadata["package"]: f for f in findings}

        assert "ring" in pkgs
        assert pkgs["ring"].extra_metadata["version"] == "0.17.5"
        assert pkgs["ring"].extra_metadata["ecosystem"] == "cargo"

        assert "rustls" in pkgs
        assert pkgs["rustls"].extra_metadata["category"] == "tls_ssl"

        assert "tokio" not in pkgs


def test_dependency_scanner_deduplication():
    scanner = DependencyScanner()
    req_content = """
cryptography==41.0.0
cryptography==41.0.0
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        req_path = os.path.join(tmpdir, "requirements.txt")
        with open(req_path, "w", encoding="utf-8") as f:
            f.write(req_content)

        findings = scanner.scan(tmpdir)
        assert len(findings) == 1
