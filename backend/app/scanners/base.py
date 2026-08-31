from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

@dataclass
class RawFinding:
    detector_name: str
    target_path: str
    file_path: str
    line_number: Optional[int]
    asset_type: AssetType
    algorithm_name: str
    purpose: CryptoPurpose
    matched_text: str
    context: str
    confidence: float = 1.0
    evidence_type: EvidenceType = EvidenceType.OBSERVED
    key_size: Optional[int] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

class BaseScanner(ABC):
    @abstractmethod
    def scan(self, target_path: str) -> List[RawFinding]:
        pass
