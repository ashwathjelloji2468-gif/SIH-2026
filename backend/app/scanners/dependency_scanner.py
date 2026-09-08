import os
import re
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Set, Tuple

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType


# Comprehensive Registry of Cryptographic Dependencies Across Ecosystems
# Format: pkg_pattern: (canonical_name, category, default_algorithm_name, default_purpose)
CRYPTO_PACKAGE_REGISTRY: Dict[str, Tuple[str, str, str, CryptoPurpose]] = {
    # Post-Quantum Cryptography (PQC)
    "pqcrypto": ("pqcrypto", "pqc", "PQC-GENERAL", CryptoPurpose.ENCRYPTION),
    "liboqs": ("liboqs", "pqc", "PQC-LIBOQS", CryptoPurpose.KEY_ESTABLISHMENT),
    "oqs": ("oqs", "pqc", "PQC-LIBOQS", CryptoPurpose.KEY_ESTABLISHMENT),
    "pqcrypto-traits": ("pqcrypto-traits", "pqc", "PQC-RUST-TRAITS", CryptoPurpose.KEY_ESTABLISHMENT),
    "circl": ("cloudflare/circl", "pqc", "PQC-CIRCL", CryptoPurpose.KEY_ESTABLISHMENT),

    # Python Crypto Ecosystem
    "cryptography": ("cryptography", "general_crypto", "CRYPTO-LIB-PYCRYPTOGRAPHY", CryptoPurpose.ENCRYPTION),
    "pycryptodome": ("pycryptodome", "general_crypto", "CRYPTO-LIB-PYCRYPTODOME", CryptoPurpose.ENCRYPTION),
    "pycryptodomex": ("pycryptodomex", "general_crypto", "CRYPTO-LIB-PYCRYPTODOMEX", CryptoPurpose.ENCRYPTION),
    "pycrypto": ("pycrypto", "general_crypto", "CRYPTO-LIB-PYCRYPTO", CryptoPurpose.ENCRYPTION),
    "m2crypto": ("m2crypto", "general_crypto", "CRYPTO-LIB-M2CRYPTO", CryptoPurpose.ENCRYPTION),
    "pynacl": ("pynacl", "general_crypto", "SODIUM-NACL", CryptoPurpose.ENCRYPTION),
    "bcrypt": ("bcrypt", "hashing", "BCRYPT", CryptoPurpose.AUTHENTICATION),
    "passlib": ("passlib", "hashing", "PASSWORD-HASHING", CryptoPurpose.AUTHENTICATION),
    "pyopenssl": ("pyopenssl", "tls_ssl", "OPENSSL", CryptoPurpose.AUTHENTICATION),
    "paramiko": ("paramiko", "tls_ssl", "SSH-CRYPTO", CryptoPurpose.AUTHENTICATION),
    "python-jose": ("python-jose", "jwt_tokens", "JOSE-JWT", CryptoPurpose.AUTHENTICATION),
    "authlib": ("authlib", "jwt_tokens", "AUTHLIB-JOSE", CryptoPurpose.AUTHENTICATION),
    "pyjwt": ("pyjwt", "jwt_tokens", "JWT", CryptoPurpose.AUTHENTICATION),
    "ecdsa": ("ecdsa", "asymmetric", "ECDSA", CryptoPurpose.SIGNATURE),
    "rsa": ("rsa", "asymmetric", "RSA", CryptoPurpose.ENCRYPTION),

    # Node.js / JavaScript / TypeScript Ecosystem
    "crypto-js": ("crypto-js", "general_crypto", "CRYPTO-JS", CryptoPurpose.ENCRYPTION),
    "node-forge": ("node-forge", "general_crypto", "FORGE-CRYPTO", CryptoPurpose.ENCRYPTION),
    "jose": ("jose", "jwt_tokens", "JOSE-JWT", CryptoPurpose.AUTHENTICATION),
    "jsonwebtoken": ("jsonwebtoken", "jwt_tokens", "JWT", CryptoPurpose.AUTHENTICATION),
    "bcryptjs": ("bcryptjs", "hashing", "BCRYPT", CryptoPurpose.AUTHENTICATION),
    "argon2": ("argon2", "hashing", "ARGON2", CryptoPurpose.AUTHENTICATION),
    "libsodium-wrappers": ("libsodium-wrappers", "general_crypto", "SODIUM", CryptoPurpose.ENCRYPTION),
    "libsodium": ("libsodium", "general_crypto", "SODIUM", CryptoPurpose.ENCRYPTION),
    "elliptic": ("elliptic", "asymmetric", "ELLIPTIC-CURVE", CryptoPurpose.KEY_ESTABLISHMENT),
    "sjcl": ("sjcl", "general_crypto", "SJCL", CryptoPurpose.ENCRYPTION),
    "subtle-crypto": ("subtle-crypto", "general_crypto", "WEBCRYPTO", CryptoPurpose.ENCRYPTION),
    "sshpk": ("sshpk", "asymmetric", "SSH-KEYS", CryptoPurpose.AUTHENTICATION),

    # Java / Maven / Gradle Ecosystem
    "bouncycastle": ("org.bouncycastle", "general_crypto", "BOUNCYCASTLE", CryptoPurpose.ENCRYPTION),
    "bcprov-jdk18on": ("org.bouncycastle:bcprov-jdk18on", "general_crypto", "BOUNCYCASTLE-PROV", CryptoPurpose.ENCRYPTION),
    "bcpkix-jdk18on": ("org.bouncycastle:bcpkix-jdk18on", "general_crypto", "BOUNCYCASTLE-PKIX", CryptoPurpose.AUTHENTICATION),
    "bcprov-jdk15on": ("org.bouncycastle:bcprov-jdk15on", "general_crypto", "BOUNCYCASTLE-PROV-LEGACY", CryptoPurpose.ENCRYPTION),
    "commons-crypto": ("org.apache.commons:commons-crypto", "general_crypto", "COMMONS-CRYPTO", CryptoPurpose.ENCRYPTION),
    "nimbus-jose-jwt": ("com.nimbusds:nimbus-jose-jwt", "jwt_tokens", "NIMBUS-JOSE-JWT", CryptoPurpose.AUTHENTICATION),
    "jjwt": ("io.jsonwebtoken:jjwt", "jwt_tokens", "JJWT", CryptoPurpose.AUTHENTICATION),
    "tink": ("com.google.crypto.tink:tink", "general_crypto", "GOOGLE-TINK", CryptoPurpose.ENCRYPTION),

    # Go Ecosystem
    "golang.org/x/crypto": ("golang.org/x/crypto", "general_crypto", "GO-X-CRYPTO", CryptoPurpose.ENCRYPTION),
    "github.com/golang-jwt/jwt": ("github.com/golang-jwt/jwt", "jwt_tokens", "GO-JWT", CryptoPurpose.AUTHENTICATION),
    "github.com/protonmail/gopenpgp": ("github.com/protonmail/gopenpgp", "asymmetric", "GOPENPGP", CryptoPurpose.ENCRYPTION),

    # Rust Ecosystem
    "ring": ("ring", "general_crypto", "RING-CRYPTO", CryptoPurpose.ENCRYPTION),
    "rustls": ("rustls", "tls_ssl", "RUSTLS", CryptoPurpose.AUTHENTICATION),
    "subtle": ("subtle", "general_crypto", "SUBTLE-CRYPTO", CryptoPurpose.ENCRYPTION),
    "ed25519-dalek": ("ed25519-dalek", "asymmetric", "ED25519-DALEK", CryptoPurpose.SIGNATURE),
    "x25519-dalek": ("x25519-dalek", "asymmetric", "X25519-DALEK", CryptoPurpose.KEY_ESTABLISHMENT),
    "sha2": ("sha2", "hashing", "SHA-2", CryptoPurpose.AUTHENTICATION),
    "sha3": ("sha3", "hashing", "SHA-3", CryptoPurpose.AUTHENTICATION),

    # PHP / Ruby / .NET
    "sodium_compat": ("paragonie/sodium_compat", "general_crypto", "SODIUM-COMPAT", CryptoPurpose.ENCRYPTION),
    "php-jwt": ("firebase/php-jwt", "jwt_tokens", "PHP-JWT", CryptoPurpose.AUTHENTICATION),
    "phpseclib": ("phpseclib/phpseclib", "general_crypto", "PHPSECLIB", CryptoPurpose.ENCRYPTION),
    "rbnacl": ("rbnacl", "general_crypto", "RBNACL", CryptoPurpose.ENCRYPTION),
    "system.security.cryptography": ("System.Security.Cryptography", "general_crypto", "DOTNET-CRYPTO", CryptoPurpose.ENCRYPTION),
}

FALLBACK_CRYPTO_KEYWORDS = [
    "crypto", "openssl", "bcrypt", "sodium", "libsodium", "pycryptodome",
    "cryptography", "hashlib", "node-forge", "jose", "jose4j", "bouncycastle",
    "ring", "nacl", "ed25519", "argon2", "jwt", "cipher", "tls", "ssl", "pqc", "oqs"
]


class DependencyScanner(BaseScanner):
    """Detect crypto-related software dependencies across multiple package ecosystems.

    Supported manifest types:
    * Python: requirements.txt, pyproject.toml, Pipfile, setup.py
    * JavaScript / TypeScript: package.json
    * Java: pom.xml, build.gradle, build.gradle.kts
    * Go: go.mod
    * Rust: Cargo.toml
    * PHP: composer.json
    * Ruby: Gemfile
    """

    def _clean_version(self, raw_ver: Optional[str]) -> Optional[str]:
        if not raw_ver:
            return None
        raw_ver = str(raw_ver).strip()
        if not raw_ver or raw_ver in ("*", "latest", "any"):
            return None
        cleaned = re.sub(r"^[=><^~@v\s]+", "", raw_ver)
        cleaned = cleaned.split(",")[0].split(";")[0].strip()
        return cleaned if cleaned else None

    def _identify_package(self, pkg_name: str) -> Tuple[str, str, str, CryptoPurpose, bool]:
        clean_name = pkg_name.strip().lower()
        
        for reg_key, (canon_name, category, algo_name, purpose) in CRYPTO_PACKAGE_REGISTRY.items():
            if reg_key in clean_name:
                return canon_name, category, algo_name, purpose, True

        for kw in FALLBACK_CRYPTO_KEYWORDS:
            if kw in clean_name:
                algo_name = f"DEP-{clean_name.upper().replace('/', '-').replace(':', '-')}"
                return pkg_name, "general_crypto", algo_name, CryptoPurpose.ENCRYPTION, False

        return pkg_name, "unknown", "UNKNOWN", CryptoPurpose.UNKNOWN, False

    def _add_finding(self, findings: List[RawFinding], seen: Set[Tuple[str, str]], target_path: str,
                     manifest_path: str, package: str, raw_version: Optional[str], ecosystem: str) -> None:
        manifest_rel = os.path.relpath(manifest_path, target_path)
        clean_pkg = package.strip()
        if not clean_pkg:
            return

        key = (manifest_rel, clean_pkg.lower())
        if key in seen:
            return
        seen.add(key)

        canon_name, category, algo_name, purpose, is_known = self._identify_package(clean_pkg)
        if category == "unknown":
            return

        version = self._clean_version(raw_version)
        matched_text = f"{clean_pkg}{'==' + version if version else ''}"

        if is_known and version:
            confidence = 1.0
        elif is_known:
            confidence = 0.9
        elif version:
            confidence = 0.85
        else:
            confidence = 0.75

        context = f"Crypto dependency '{clean_pkg}' ({category}) in {ecosystem} manifest '{manifest_rel}'"

        extra_metadata: Dict[str, Any] = {
            "package": clean_pkg,
            "canonical_name": canon_name,
            "version": version,
            "raw_version_spec": raw_version,
            "ecosystem": ecosystem,
            "manifest": manifest_rel,
            "category": category,
            "purpose": purpose.value if hasattr(purpose, "value") else str(purpose),
            "is_pqc": (category == "pqc"),
            "file_path": manifest_rel,
        }

        findings.append(RawFinding(
            detector_name="DependencyScanner",
            target_path=target_path,
            file_path=manifest_rel,
            line_number=1,
            asset_type=AssetType.DEPENDENCY,
            algorithm_name=algo_name,
            purpose=purpose,
            matched_text=matched_text,
            context=context,
            confidence=confidence,
            evidence_type=EvidenceType.OBSERVED,
            extra_metadata=extra_metadata,
        ))

    # -------------------- Python --------------------
    def _scan_requirements_txt(self, path: str, target_path: str, findings: List[RawFinding], seen: Set[Tuple[str, str]]):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue
                    # Split package and version operators
                    match = re.split(r"(==|>=|<=|~=|>|<|~=)", line)
                    pkg = match[0].split("[")[0].strip()
                    ver = match[2].strip() if len(match) >= 3 else None
                    self._add_finding(findings, seen, target_path, path, pkg, ver, "python")
        except Exception:
            pass

    def _scan_pyproject_toml(self, path: str, target_path: str, findings: List[RawFinding], seen: Set[Tuple[str, str]]):
        try:
            if tomllib is not None:
                with open(path, "rb") as f:
                    data = tomllib.load(f)
                deps = data.get("project", {}).get("dependencies", [])
                for dep in deps:
                    match = re.split(r"(==|>=|<=|~=|>|<)", dep)
                    pkg = match[0].split("[")[0].strip()
                    ver = match[2].strip() if len(match) >= 3 else None
                    self._add_finding(findings, seen, target_path, path, pkg, ver, "python")

                poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
                for pkg, ver_spec in poetry_deps.items():
                    ver = ver_spec if isinstance(ver_spec, str) else ver_spec.get("version") if isinstance(ver_spec, dict) else None
                    self._add_finding(findings, seen, target_path, path, pkg, ver, "python")
            else:
                # Fallback line regex for pyproject.toml
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "=" in line:
                            parts = line.split("=", 1)
                            pkg = parts[0].strip().strip('"\'')
                            ver = parts[1].strip().strip('"\'')
                            self._add_finding(findings, seen, target_path, path, pkg, ver, "python")
        except Exception:
            pass

    def _scan_pipfile(self, path: str, target_path: str, findings: List[RawFinding], seen: Set[Tuple[str, str]]):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for section in ("default", "develop", "packages", "dev-packages"):
                for pkg, meta in data.get(section, {}).items():
                    version = meta.get("version") if isinstance(meta, dict) else str(meta)
                    self._add_finding(findings, seen, target_path, path, pkg, version, "python")
        except Exception:
            pass

    # -------------------- JavaScript / Node --------------------
    def _scan_package_json(self, path: str, target_path: str, findings: List[RawFinding], seen: Set[Tuple[str, str]]):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for dep_section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                for pkg, version in data.get(dep_section, {}).items():
                    self._add_finding(findings, seen, target_path, path, pkg, str(version), "npm")
        except Exception:
            pass

    # -------------------- Java (Maven & Gradle) --------------------
    def _scan_pom_xml(self, path: str, target_path: str, findings: List[RawFinding], seen: Set[Tuple[str, str]]):
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            ns = {"m": root.tag.split('}')[0].strip('{')} if "}" in root.tag else {}
            for dep in root.findall('.//m:dependency', ns) if ns else root.findall('.//dependency'):
                group_id = dep.find('m:groupId', ns) if ns else dep.find('groupId')
                artifact_id = dep.find('m:artifactId', ns) if ns else dep.find('artifactId')
                version = dep.find('m:version', ns) if ns else dep.find('version')
                if group_id is not None and artifact_id is not None and group_id.text and artifact_id.text:
                    pkg = f"{group_id.text.strip()}:{artifact_id.text.strip()}"
                    ver = version.text.strip() if version is not None and version.text else None
                    self._add_finding(findings, seen, target_path, path, pkg, ver, "maven")
        except Exception:
            pass

    def _scan_gradle(self, path: str, target_path: str, findings: List[RawFinding], seen: Set[Tuple[str, str]]):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    match = re.search(r"['\"]([a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+)(?::([a-zA-Z0-9._-]+))?['\"]", line)
                    if match:
                        pkg = match.group(1)
                        ver = match.group(2)
                        self._add_finding(findings, seen, target_path, path, pkg, ver, "gradle")
        except Exception:
            pass

    # -------------------- Go --------------------
    def _scan_go_mod(self, path: str, target_path: str, findings: List[RawFinding], seen: Set[Tuple[str, str]]):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("require") or line.startswith("replace") or "/" in line:
                        parts = line.replace("require", "").replace("replace", "").strip().split()
                        if len(parts) >= 1:
                            pkg = parts[0]
                            ver = parts[1] if len(parts) >= 2 else None
                            self._add_finding(findings, seen, target_path, path, pkg, ver, "go")
        except Exception:
            pass

    # -------------------- Rust --------------------
    def _scan_cargo_toml(self, path: str, target_path: str, findings: List[RawFinding], seen: Set[Tuple[str, str]]):
        try:
            if tomllib is not None:
                with open(path, "rb") as f:
                    data = tomllib.load(f)
                for dep_section in ("dependencies", "dev-dependencies", "build-dependencies"):
                    for pkg, meta in data.get(dep_section, {}).items():
                        version = meta if isinstance(meta, str) else meta.get("version") if isinstance(meta, dict) else None
                        self._add_finding(findings, seen, target_path, path, pkg, version, "cargo")
            else:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "=" in line:
                            parts = line.split("=", 1)
                            pkg = parts[0].strip()
                            ver = parts[1].strip().strip('"\'')
                            self._add_finding(findings, seen, target_path, path, pkg, ver, "cargo")
        except Exception:
            pass

    # -------------------- PHP & Ruby --------------------
    def _scan_composer_json(self, path: str, target_path: str, findings: List[RawFinding], seen: Set[Tuple[str, str]]):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for dep_section in ("require", "require-dev"):
                for pkg, version in data.get(dep_section, {}).items():
                    self._add_finding(findings, seen, target_path, path, pkg, str(version), "composer")
        except Exception:
            pass

    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        seen: Set[Tuple[str, str]] = set()

        if not os.path.isdir(target_path):
            return findings

        for root, _, files in os.walk(target_path):
            for file in files:
                full_path = os.path.join(root, file)

                if file == "requirements.txt" or file.endswith(".requirements.txt"):
                    self._scan_requirements_txt(full_path, target_path, findings, seen)
                elif file == "pyproject.toml":
                    self._scan_pyproject_toml(full_path, target_path, findings, seen)
                elif file == "Pipfile":
                    self._scan_pipfile(full_path, target_path, findings, seen)
                elif file == "package.json":
                    self._scan_package_json(full_path, target_path, findings, seen)
                elif file == "pom.xml":
                    self._scan_pom_xml(full_path, target_path, findings, seen)
                elif file in ("build.gradle", "build.gradle.kts"):
                    self._scan_gradle(full_path, target_path, findings, seen)
                elif file == "go.mod":
                    self._scan_go_mod(full_path, target_path, findings, seen)
                elif file == "Cargo.toml":
                    self._scan_cargo_toml(full_path, target_path, findings, seen)
                elif file == "composer.json":
                    self._scan_composer_json(full_path, target_path, findings, seen)

        return findings
