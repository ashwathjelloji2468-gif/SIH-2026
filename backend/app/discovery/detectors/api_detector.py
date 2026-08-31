from typing import List
from app.scanners.base import RawFinding

class APIDetector:
    def detect(self, findings: List[RawFinding]) -> List[RawFinding]:
        return [f for f in findings if f.asset_type.value == "API_CALL"]

class ConfigDetector:
    def detect(self, findings: List[RawFinding]) -> List[RawFinding]:
        return []

class LibraryDetector:
    def detect(self, findings: List[RawFinding]) -> List[RawFinding]:
        return [f for f in findings if f.asset_type.value == "DEPENDENCY"]

class ProtocolDetector:
    def detect(self, findings: List[RawFinding]) -> List[RawFinding]:
        return []

class CertificateDetector:
    def detect(self, findings: List[RawFinding]) -> List[RawFinding]:
        return [f for f in findings if f.asset_type.value == "CERTIFICATE"]
