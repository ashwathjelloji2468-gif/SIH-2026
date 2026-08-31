from typing import List
from app.evidence.evidence_types import RawEvidence
from app.evidence.confidence import calculate_confidence_score
from app.evidence.provenance import create_provenance

class EvidenceEngine:
    def process_evidence(self, scan_id: str, raw_item: RawEvidence) -> RawEvidence:
        provenance = create_provenance(scan_id, raw_item.detector_name, raw_item.detector_version)
        confidence = calculate_confidence_score(
            evidence_type=raw_item.evidence_type,
            detector_accuracy=0.95,
            has_ast_validation=(raw_item.excerpt is not None and "import" in raw_item.excerpt.lower())
        )
        
        raw_item.confidence_score = confidence
        raw_item.provenance = provenance
        return raw_item
