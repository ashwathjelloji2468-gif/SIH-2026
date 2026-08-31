from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from app.models.enums import EvidenceType

@dataclass
class RawEvidence:
    evidence_type: EvidenceType
    source_file: str
    detector_name: str
    detector_version: str = "1.0.0"
    line_number: Optional[int] = None
    excerpt: Optional[str] = None
    confidence_score: float = 1.0
    provenance: Dict[str, Any] = field(default_factory=dict)
