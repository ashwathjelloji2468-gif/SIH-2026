import os
import subprocess
import json
import shutil
import re
from typing import List, Optional, Dict, Any, Tuple

from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

# Comprehensive registry of crypto-related packages, libraries, tools, and language packages
CRYPTO_PACKAGE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # OpenSSL family
    "openssl": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "system", "category": "tls_library"},
    "libssl": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "system", "category": "tls_library"},
    "libssl-dev": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "tls_library"},
    "libssl-devel": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "redhat", "category": "tls_library"},
    "libssl3": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "tls_library"},
    "libssl1.1": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "tls_library"},
    "libcrypto": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "system", "category": "crypto_core"},
    "libcrypto++": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "system", "category": "crypto_core"},
    "openssl-devel": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "redhat", "category": "tls_library"},
    "openssl-libs": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "redhat", "category": "tls_library"},

    # GnuTLS / Libgcrypt / NSS
    "gnutls": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "system", "category": "tls_library"},
    "gnutls-bin": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "tls_library"},
    "libgnutls28-dev": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "tls_library"},
    "libgnutls-devel": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "redhat", "category": "tls_library"},
    "libgcrypt": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "system", "category": "crypto_core"},
    "libgcrypt20": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "crypto_core"},
    "libgcrypt20-dev": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "crypto_core"},
    "libnss3": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "tls_library"},
    "libnss3-dev": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "tls_library"},
    "nss": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "system", "category": "tls_library"},
    "nss-devel": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "redhat", "category": "tls_library"},

    # NIST PQC & Post-Quantum Libraries
    "liboqs": {"purpose": CryptoPurpose.KEY_ESTABLISHMENT, "ecosystem": "pqc", "category": "pqc_library"},
    "liboqs-dev": {"purpose": CryptoPurpose.KEY_ESTABLISHMENT, "ecosystem": "pqc", "category": "pqc_library"},
    "oqs-provider": {"purpose": CryptoPurpose.KEY_ESTABLISHMENT, "ecosystem": "pqc", "category": "pqc_provider"},
    "pqcrypto": {"purpose": CryptoPurpose.KEY_ESTABLISHMENT, "ecosystem": "python", "category": "pqc_library"},

    # WolfSSL / MbedTLS / Libsodium / Botan / Crypto++
    "wolfssl": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "system", "category": "tls_library"},
    "libwolfssl-dev": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "tls_library"},
    "mbedtls": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "system", "category": "tls_library"},
    "libmbedtls-dev": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "tls_library"},
    "libsodium": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "system", "category": "crypto_core"},
    "libsodium-dev": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "crypto_core"},
    "libsodium-devel": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "redhat", "category": "crypto_core"},
    "botan": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "system", "category": "crypto_core"},
    "libbotan-2-dev": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "crypto_core"},
    "crypto++": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "system", "category": "crypto_core"},
    "libcrypto++-dev": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "debian", "category": "crypto_core"},

    # PKI Certificates, Keys & SSH
    "ca-certificates": {"purpose": CryptoPurpose.AUTHENTICATION, "ecosystem": "system", "category": "pki_cert"},
    "openssh-client": {"purpose": CryptoPurpose.AUTHENTICATION, "ecosystem": "system", "category": "ssh"},
    "openssh-server": {"purpose": CryptoPurpose.AUTHENTICATION, "ecosystem": "system", "category": "ssh"},
    "certbot": {"purpose": CryptoPurpose.AUTHENTICATION, "ecosystem": "python", "category": "pki_cert"},

    # Language Ecosystem Crypto Packages
    "pycryptodome": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "python", "category": "crypto_lib"},
    "pycryptodomex": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "python", "category": "crypto_lib"},
    "cryptography": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "python", "category": "crypto_lib"},
    "m2crypto": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "python", "category": "crypto_lib"},
    "bouncycastle": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "java", "category": "crypto_lib"},
    "org.bouncycastle": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "java", "category": "crypto_lib"},
    "golang.org/x/crypto": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "go", "category": "crypto_lib"},
    "rustls": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "rust", "category": "tls_library"},
    "ring": {"purpose": CryptoPurpose.ENCRYPTION, "ecosystem": "rust", "category": "crypto_lib"},
}

PACKAGE_MANAGER_PATTERNS = [
    (re.compile(r"\bapt(?:-get)?\s+install\b", re.IGNORECASE), "apt", "debian"),
    (re.compile(r"\bapk\s+add\b", re.IGNORECASE), "apk", "alpine"),
    (re.compile(r"\b(?:yum|dnf|microdnf)\s+install\b", re.IGNORECASE), "dnf", "redhat"),
    (re.compile(r"\bpacman\s+-S\b", re.IGNORECASE), "pacman", "arch"),
    (re.compile(r"\bzypper\s+install\b", re.IGNORECASE), "zypper", "suse"),
    (re.compile(r"\bpip3?\s+install\b", re.IGNORECASE), "pip", "python"),
    (re.compile(r"\b(?:npm\s+install|yarn\s+add)\b", re.IGNORECASE), "npm", "javascript"),
    (re.compile(r"\bcargo\s+install\b", re.IGNORECASE), "cargo", "rust"),
    (re.compile(r"\bgo\s+(?:get|install)\b", re.IGNORECASE), "go", "golang"),
]

class ContainerScanner(BaseScanner):
    """Detect crypto-related components, base images, libraries, and package specifications
    in Docker containers, Dockerfiles, and container SBOMs.

    * Performs static AST/line analysis of Dockerfiles (and Dockerfile variants).
    * Extracts base images, tags, package manager commands, and crypto package versions.
    * Optionally runs `syft` binary (if installed) to extract Software Bill of Materials (SBOM).
    * Produces rich RawFinding objects with complete extra_metadata and confidence scoring.
    """

    def _add_finding(
        self,
        findings: List[RawFinding],
        target_path: str,
        manifest_rel_path: str,
        name: str,
        purpose: CryptoPurpose,
        evidence_type: EvidenceType,
        confidence: float,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        context_msg = f"Container component detected: {name}"
        if extra and extra.get("version"):
            context_msg += f" (version: {extra['version']})"
        if extra and extra.get("base_image"):
            context_msg += f" [Base: {extra['base_image']}]"

        findings.append(RawFinding(
            detector_name="ContainerScanner",
            target_path=target_path,
            file_path=manifest_rel_path,
            line_number=extra.get("dockerfile_line") if extra else 0,
            asset_type=AssetType.CONTAINER,
            algorithm_name=name,
            purpose=purpose,
            matched_text=name,
            context=context_msg,
            confidence=confidence,
            evidence_type=evidence_type,
            extra_metadata=extra or {},
        ))

    def _parse_package_token(self, token: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse package token into (package_name, version) if present."""
        clean_token = token.strip().strip("'\"\\;,")
        if not clean_token or clean_token.startswith("-"):
            return None, None

        # Match tokens like openssl=3.0.2-0ubuntu1 or pycryptodome==3.18.0 or openssl:3.1.2
        match = re.match(r"^([a-zA-Z0-9_\-\.\:\/]+)(?:[=><~:]+([a-zA-Z0-9_\-\.\+]+))?$", clean_token)
        if match:
            pkg_name = match.group(1).lower()
            version = match.group(2)
            return pkg_name, version
        return None, None

    def _scan_dockerfile(self, dockerfile_path: str, target_path: str, findings: List[RawFinding]) -> Optional[str]:
        rel_path = os.path.relpath(dockerfile_path, target_path)
        try:
            with open(dockerfile_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            return None

        base_image: Optional[str] = None
        seen_packages: set = set()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # 1. Base Image FROM instruction
            if stripped.upper().startswith("FROM "):
                parts = stripped.split()
                if len(parts) >= 2:
                    raw_image = parts[1]
                    if raw_image and raw_image != "scratch":
                        if base_image is None:
                            base_image = raw_image

                        image_tag = None
                        if ":" in raw_image:
                            img_parts = raw_image.split(":", 1)
                            image_name, image_tag = img_parts[0], img_parts[1]
                        else:
                            image_name = raw_image

                        self._add_finding(
                            findings,
                            target_path,
                            rel_path,
                            name=raw_image,
                            purpose=CryptoPurpose.UNKNOWN,
                            evidence_type=EvidenceType.OBSERVED,
                            confidence=0.85,
                            extra={
                                "dockerfile_line": idx,
                                "type": "base_image",
                                "base_image": raw_image,
                                "image_name": image_name,
                                "image_tag": image_tag,
                                "source": "dockerfile",
                            },
                        )

            # 2. RUN package installation commands
            for pm_regex, pm_type, default_eco in PACKAGE_MANAGER_PATTERNS:
                if pm_regex.search(stripped):
                    # Tokenize line to find package names and versions
                    tokens = stripped.replace("&&", " ").replace("\\", " ").split()
                    for token in tokens:
                        pkg_name, pkg_version = self._parse_package_token(token)
                        if not pkg_name:
                            continue

                        # Check if token is a known crypto package or substring match
                        matched_reg = None
                        if pkg_name in CRYPTO_PACKAGE_REGISTRY:
                            matched_reg = CRYPTO_PACKAGE_REGISTRY[pkg_name]
                        else:
                            for reg_pkg, reg_info in CRYPTO_PACKAGE_REGISTRY.items():
                                if reg_pkg in pkg_name:
                                    matched_reg = reg_info
                                    break

                        if matched_reg:
                            pkg_key = (pkg_name, pkg_version, idx)
                            if pkg_key in seen_packages:
                                continue
                            seen_packages.add(pkg_key)

                            confidence = 0.95 if pkg_version else 0.85
                            purpose = matched_reg.get("purpose", CryptoPurpose.UNKNOWN)
                            ecosystem = matched_reg.get("ecosystem", default_eco)

                            self._add_finding(
                                findings,
                                target_path,
                                rel_path,
                                name=pkg_name,
                                purpose=purpose,
                                evidence_type=EvidenceType.INFERRED,
                                confidence=confidence,
                                extra={
                                    "package_name": pkg_name,
                                    "version": pkg_version,
                                    "base_image": base_image,
                                    "dockerfile_line": idx,
                                    "install_command": stripped,
                                    "package_manager": pm_type,
                                    "ecosystem": ecosystem,
                                    "category": matched_reg.get("category"),
                                    "source": "dockerfile",
                                },
                            )

        return base_image

    def _scan_image_syft(self, image_name: str, target_path: str, findings: List[RawFinding]) -> None:
        """Optional Syft integration: runs `syft <image> -o json` if syft binary is available."""
        syft_path = shutil.which("syft")
        if not syft_path:
            return

        try:
            result = subprocess.run(
                [syft_path, image_name, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0 or not result.stdout:
                return
            sbom = json.loads(result.stdout)
        except Exception:
            return

        syft_version = sbom.get("descriptor", {}).get("version") or sbom.get("metadata", {}).get("tool", {}).get("version")
        for artifact in sbom.get("artifacts", []):
            name = artifact.get("name", "").lower()
            version = artifact.get("version")
            artifact_type = artifact.get("type", "unknown")

            matched_reg = None
            if name in CRYPTO_PACKAGE_REGISTRY:
                matched_reg = CRYPTO_PACKAGE_REGISTRY[name]
            else:
                for reg_pkg, reg_info in CRYPTO_PACKAGE_REGISTRY.items():
                    if reg_pkg in name:
                        matched_reg = reg_info
                        break

            if matched_reg:
                purpose = matched_reg.get("purpose", CryptoPurpose.UNKNOWN)
                self._add_finding(
                    findings,
                    target_path,
                    f"syft:{image_name}",
                    name=artifact.get("name") or name,
                    purpose=purpose,
                    evidence_type=EvidenceType.OBSERVED,
                    confidence=0.95,
                    extra={
                        "package_name": name,
                        "version": version,
                        "package_type": artifact_type,
                        "syft_version": syft_version,
                        "licenses": [l.get("value") for l in artifact.get("licenses", []) if isinstance(l, dict)],
                        "source": "syft",
                    },
                )

    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        if not os.path.exists(target_path):
            return findings

        # Find all Dockerfiles, Containerfiles, and dockerfile variants
        dockerfiles: List[str] = []
        if os.path.isfile(target_path):
            filename = os.path.basename(target_path).lower()
            if "dockerfile" in filename or "containerfile" in filename:
                dockerfiles.append(target_path)
        else:
            for root, _, files in os.walk(target_path):
                for file in files:
                    lowered = file.lower()
                    if "dockerfile" in lowered or "containerfile" in lowered:
                        dockerfiles.append(os.path.join(root, file))

        first_base_image: Optional[str] = None
        for df in dockerfiles:
            base_img = self._scan_dockerfile(df, target_path, findings)
            if not first_base_image and base_img:
                first_base_image = base_img

        # If base image was detected and syft is available, run SBOM scan
        if first_base_image:
            self._scan_image_syft(first_base_image, target_path, findings)

        return findings
