import os
from typing import List
from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

class DependencyScanner(BaseScanner):
    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        req_file = os.path.join(target_path, "requirements.txt")
        if os.path.exists(req_file):
            try:
                with open(req_file, "r") as f:
                    for idx, line in enumerate(f.readlines(), start=1):
                        if "pycryptodome" in line.lower() or "cryptography" in line.lower():
                            findings.append(RawFinding(
                                detector_name="DependencyScanner",
                                target_path=target_path,
                                file_path="requirements.txt",
                                line_number=idx,
                                asset_type=AssetType.DEPENDENCY,
                                algorithm_name="CryptoLibrary",
                                purpose=CryptoPurpose.UNKNOWN,
                                matched_text=line.strip(),
                                context=f"Cryptographic dependency found: {line.strip()}",
                                confidence=0.90,
                                evidence_type=EvidenceType.OBSERVED
                            ))
            except Exception:
                pass
        return findings
