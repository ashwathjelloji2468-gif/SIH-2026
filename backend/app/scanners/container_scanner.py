import os
import subprocess
import json
import shutil
from typing import List, Optional

from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

CRYPTO_PACKAGES = [
    "openssl",
    "libssl",
    "libcrypto",
    "gnutls",
    "libgcrypt",
]

class ContainerScanner(BaseScanner):
    """Detect crypto‑related components in Docker containers.

    * Parses a local Dockerfile (if present) to extract the base image and any
      package install commands that mention known crypto packages.
    * If the `syft` binary is available, optionally runs `syft <image> -o json`
      to obtain a Software Bill of Materials (SBOM) and extracts crypto‑related
      packages from it.
    The scanner never fabricates an algorithm; it only reports the observed
    components with appropriate evidence_type and confidence.
    """

    def _add_finding(self, findings: List[RawFinding], target_path: str, manifest: str,
                     name: str, purpose: CryptoPurpose, evidence_type: EvidenceType,
                     confidence: float, extra: Optional[dict] = None) -> None:
        findings.append(RawFinding(
            detector_name="ContainerScanner",
            target_path=target_path,
            file_path=manifest,
            line_number=0,
            asset_type=AssetType.CONTAINER,
            algorithm_name=name,
            purpose=purpose,
            matched_text=name,
            context=f"Container component detected: {name}",
            confidence=confidence,
            evidence_type=evidence_type,
            extra_metadata=extra or {},
        ))

    def _scan_dockerfile(self, dockerfile_path: str, target_path: str, findings: List[RawFinding]):
        try:
            with open(dockerfile_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            return
        base_image = None
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.upper().startswith("FROM ") and base_image is None:
                base_image = stripped.split()[1]
                self._add_finding(
                    findings, target_path, os.path.relpath(dockerfile_path, target_path),
                    name=base_image,
                    purpose=CryptoPurpose.UNKNOWN,
                    evidence_type=EvidenceType.OBSERVED,
                    confidence=0.9,
                    extra={"dockerfile_line": idx, "type": "base_image"},
                )
            # Look for package install commands
            lowered = stripped.lower()
            if any(cmd in lowered for cmd in ["apt-get install", "apk add", "yum install", "dnf install", "pacman -S"]):
                for pkg in CRYPTO_PACKAGES:
                    if pkg in lowered:
                        self._add_finding(
                            findings, target_path, os.path.relpath(dockerfile_path, target_path),
                            name=pkg,
                            purpose=CryptoPurpose.UNKNOWN,
                            evidence_type=EvidenceType.INFERRED,
                            confidence=0.8,
                            extra={"dockerfile_line": idx, "install_command": stripped},
                        )

    def _scan_image_syft(self, image_name: str, target_path: str, findings: List[RawFinding]):
        syft_path = shutil.which("syft")
        if not syft_path:
            return
        try:
            result = subprocess.run([syft_path, image_name, "-o", "json"], capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return
            sbom = json.loads(result.stdout)
        except Exception:
            return
        # sbom['artifacts'] contains package list
        for artifact in sbom.get("artifacts", []):
            name = artifact.get("name", "").lower()
            if any(crypto_pkg in name for crypto_pkg in CRYPTO_PACKAGES):
                self._add_finding(
                    findings, target_path, f"syft:{image_name}",
                    name=artifact.get("name"),
                    purpose=CryptoPurpose.UNKNOWN,
                    evidence_type=EvidenceType.OBSERVED,
                    confidence=0.95,
                    extra={"syft_version": sbom.get("metadata", {}).get("tool", {}).get("version")},
                )

    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        if not os.path.isdir(target_path):
            return findings
        dockerfile = os.path.join(target_path, "Dockerfile")
        base_image = None
        if os.path.isfile(dockerfile):
            self._scan_dockerfile(dockerfile, target_path, findings)
            # Attempt to extract the base image from the first FROM line for syft scanning
            try:
                with open(dockerfile, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().upper().startswith("FROM "):
                            base_image = line.strip().split()[1]
                            break
            except Exception:
                pass
        # If we have a base image and syft is available, run SBOM analysis
        if base_image:
            self._scan_image_syft(base_image, target_path, findings)
        return findings
