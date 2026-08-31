from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.db_models import Evidence
from app.models.enums import EvidenceType

class FindingRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_evidence(
        self,
        asset_id: str,
        evidence_type: EvidenceType,
        source_file: str,
        detector_name: str,
        detector_version: str = "1.0.0",
        excerpt: Optional[str] = None,
        line_number: Optional[int] = None,
        confidence_score: float = 1.0,
        provenance: Optional[dict] = None
    ) -> Evidence:
        db_obj = Evidence(
            asset_id=asset_id,
            evidence_type=evidence_type,
            source_file=source_file,
            line_number=line_number,
            detector_name=detector_name,
            detector_version=detector_version,
            excerpt=excerpt,
            confidence_score=confidence_score,
            provenance=provenance
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_asset(self, asset_id: str) -> List[Evidence]:
        return self.db.query(Evidence).filter(Evidence.asset_id == asset_id).all()
