from typing import List
from app.scanners.base import RawFinding

class AlgorithmDetector:
    def detect(self, findings: List[RawFinding]) -> List[RawFinding]:
        return [f for f in findings if f.algorithm_name != "UNKNOWN"]
