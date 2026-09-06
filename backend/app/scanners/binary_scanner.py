import os
import subprocess
import re
from typing import List
from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

class BinaryScanner(BaseScanner):
    """Scans compiled binaries for embedded cryptographic identifiers.

    Walks the target directory, looks for typical binary extensions and extracts
    printable strings using the `strings` utility (available on macOS). Detected
    keywords are mapped to algorithms and purposes, producing RawFinding objects.
    """

    BINARY_EXTS = (".so", ".dll", ".dylib", ".exe")
    PATTERNS = [
        (re.compile(r"RSA", re.IGNORECASE), "RSA", CryptoPurpose.SIGNATURE, AssetType.ALGORITHM),
        (re.compile(r"AES", re.IGNORECASE), "AES", CryptoPurpose.ENCRYPTION, AssetType.ALGORITHM),
        (re.compile(r"SHA-?256", re.IGNORECASE), "SHA-256", CryptoPurpose.HASHING, AssetType.ALGORITHM),
    ]

    def _extract_strings(self, file_path: str) -> List[str]:
        try:
            result = subprocess.run(["strings", file_path], capture_output=True, text=True, timeout=5)
            return result.stdout.splitlines()
        except Exception:
            return []

    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        if not os.path.isdir(target_path):
            return findings
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith(self.BINARY_EXTS):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, target_path)
                    for line in self._extract_strings(full_path):
                        for regex, alg, purpose, asset_type in self.PATTERNS:
                            if regex.search(line):
                                findings.append(RawFinding(
                                    detector_name="BinaryScanner",
                                    target_path=target_path,
                                    file_path=rel_path,
                                    line_number=1,
                                    asset_type=asset_type,
                                    algorithm_name=alg,
                                    purpose=purpose,
                                    matched_text=line.strip(),
                                    context=f"Binary string match for {alg}",
                                    confidence=0.85,
                                    evidence_type=EvidenceType.OBSERVED,
                                ))
        return findings
