import os
from typing import List
from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

class ContainerScanner(BaseScanner):
    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        dockerfile = os.path.join(target_path, "Dockerfile")
        if os.path.exists(dockerfile):
            findings.append(RawFinding(
                detector_name="ContainerScanner",
                target_path=target_path,
                file_path="Dockerfile",
                line_number=1,
                asset_type=AssetType.CONTAINER,
                algorithm_name="OpenSSL",
                purpose=CryptoPurpose.UNKNOWN,
                matched_text="Dockerfile",
                context="Container base image scan",
                confidence=0.80,
                evidence_type=EvidenceType.INFERRED
            ))
        return findings
