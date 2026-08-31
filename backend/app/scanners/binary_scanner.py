from typing import List
from app.scanners.base import BaseScanner, RawFinding

class BinaryScanner(BaseScanner):
    def scan(self, target_path: str) -> List[RawFinding]:
        return []
