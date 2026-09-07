import os
import json
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None
import xml.etree.ElementTree as ET
from typing import List, Optional

from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

CRYPTO_KEYWORDS = [
    "crypto",
    "openssl",
    "bcrypt",
    "sodium",
    "libsodium",
    "pycryptodome",
    "cryptography",
    "hashlib",
    "node-forge",
    "jose",
    "jose4j",
    "bouncycastle",
    "golang.org/x/crypto",
    "ring",
    "nacl",
    "ed25519",
]

class DependencyScanner(BaseScanner):
    """Detect crypto‑related dependencies across multiple ecosystems.

    Supported manifest types:
    * Python – requirements.txt, pyproject.toml, Pipfile
    * JavaScript/TypeScript – package.json
    * Java (Maven) – pom.xml
    * Go – go.mod
    * Rust – Cargo.toml
    """

    def _add_finding(self, findings: List[RawFinding], target_path: str, manifest_path: str,
                     package: str, version: Optional[str], ecosystem: str) -> None:
        findings.append(RawFinding(
            detector_name="DependencyScanner",
            target_path=target_path,
            file_path=manifest_path,
            line_number=0,
            asset_type=AssetType.DEPENDENCY,
            algorithm_name="UNKNOWN",
            purpose=CryptoPurpose.UNKNOWN,
            matched_text=f"{package}{'==' + version if version else ''}",
            context=f"Detected crypto‑related dependency in {ecosystem}: {package}",
            confidence=0.8,
            evidence_type=EvidenceType.INFERRED,
            extra_metadata={
                "package": package,
                "version": version,
                "ecosystem": ecosystem,
                "manifest": manifest_path,
            },
        ))

    # -------------------- Python --------------------
    def _scan_requirements_txt(self, path: str, target_path: str, findings: List[RawFinding]):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    pkg = line.strip().split("==")[0]
                    if any(kw in pkg.lower() for kw in CRYPTO_KEYWORDS):
                        version = line.strip().split("==")[1] if "==" in line else None
                        self._add_finding(findings, target_path, os.path.relpath(path, target_path), pkg, version, "python")
        except Exception:
            pass

    def _scan_pyproject_toml(self, path: str, target_path: str, findings: List[RawFinding]):
        if tomllib is None:
            return
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            deps = data.get("project", {}).get("dependencies", [])
            for dep in deps:
                pkg = dep.split("[")[0].split("==")[0].strip()
                if any(kw in pkg.lower() for kw in CRYPTO_KEYWORDS):
                    version = dep.split("==")[1].strip() if "==" in dep else None
                    self._add_finding(findings, target_path, os.path.relpath(path, target_path), pkg, version, "python")
        except Exception:
            pass

    def _scan_pipfile(self, path: str, target_path: str, findings: List[RawFinding]):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for section in ("default", "develop"):
                for pkg, meta in data.get(section, {}).items():
                    if any(kw in pkg.lower() for kw in CRYPTO_KEYWORDS):
                        version = meta.get("version") if isinstance(meta, dict) else None
                        self._add_finding(findings, target_path, os.path.relpath(path, target_path), pkg, version, "python")
        except Exception:
            pass

    # -------------------- JavaScript --------------------
    def _scan_package_json(self, path: str, target_path: str, findings: List[RawFinding]):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for dep_section in ("dependencies", "devDependencies", "optionalDependencies"):
                for pkg, version in data.get(dep_section, {}).items():
                    if any(kw in pkg.lower() for kw in CRYPTO_KEYWORDS):
                        self._add_finding(findings, target_path, os.path.relpath(path, target_path), pkg, version, "npm")
        except Exception:
            pass

    # -------------------- Java (Maven) --------------------
    def _scan_pom_xml(self, path: str, target_path: str, findings: List[RawFinding]):
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            ns = {"m": root.tag.split('}')[0].strip('{')} if "}" in root.tag else {}
            for dep in root.findall('.//m:dependency', ns):
                group_id = dep.find('m:groupId', ns)
                artifact_id = dep.find('m:artifactId', ns)
                version = dep.find('m:version', ns)
                if group_id is not None and artifact_id is not None:
                    pkg = f"{group_id.text}:{artifact_id.text}".strip()
                    if any(kw in pkg.lower() for kw in CRYPTO_KEYWORDS):
                        ver = version.text if version is not None else None
                        self._add_finding(findings, target_path, os.path.relpath(path, target_path), pkg, ver, "maven")
        except Exception:
            pass

    # -------------------- Go --------------------
    def _scan_go_mod(self, path: str, target_path: str, findings: List[RawFinding]):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("require") or line.startswith("replace"):
                        parts = line.split()
                        if len(parts) >= 2:
                            pkg = parts[1]
                            if any(kw in pkg.lower() for kw in CRYPTO_KEYWORDS):
                                self._add_finding(findings, target_path, os.path.relpath(path, target_path), pkg, None, "go")
        except Exception:
            pass

    # -------------------- Rust --------------------
    def _scan_cargo_toml(self, path: str, target_path: str, findings: List[RawFinding]):
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            for dep_section in ("dependencies", "dev-dependencies", "build-dependencies"):
                for pkg, meta in data.get(dep_section, {}).items():
                    if any(kw in pkg.lower() for kw in CRYPTO_KEYWORDS):
                        version = meta if isinstance(meta, str) else meta.get("version")
                        self._add_finding(findings, target_path, os.path.relpath(path, target_path), pkg, version, "cargo")
        except Exception:
            pass

    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        if not os.path.isdir(target_path):
            return findings
        for root, _, files in os.walk(target_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, target_path)
                if file == "requirements.txt":
                    self._scan_requirements_txt(full_path, target_path, findings)
                elif file == "pyproject.toml":
                    self._scan_pyproject_toml(full_path, target_path, findings)
                elif file == "Pipfile":
                    self._scan_pipfile(full_path, target_path, findings)
                elif file == "package.json":
                    self._scan_package_json(full_path, target_path, findings)
                elif file == "pom.xml":
                    self._scan_pom_xml(full_path, target_path, findings)
                elif file == "go.mod":
                    self._scan_go_mod(full_path, target_path, findings)
                elif file == "Cargo.toml":
                    self._scan_cargo_toml(full_path, target_path, findings)
        return findings
