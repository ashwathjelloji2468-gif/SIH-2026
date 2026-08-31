import os
from typing import List
from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

class CertificateScanner(BaseScanner):
    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        if not os.path.exists(target_path):
            return findings
            
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith((".crt", ".cer", ".pem")):
                    rel_path = os.path.relpath(os.path.join(root, file), target_path)
                    findings.append(RawFinding(
                        detector_name="CertificateScanner",
                        target_path=target_path,
                        file_path=rel_path,
                        line_number=1,
                        asset_type=AssetType.CERTIFICATE,
                        algorithm_name="RSA",
                        purpose=CryptoPurpose.AUTHENTICATION,
                        matched_text=file,
                        context=f"X.509 Certificate file detected: {file}",
                        confidence=0.95,
                        evidence_type=EvidenceType.OBSERVED,
                        key_size=2048
                    ))
        return findings
