from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.db_models import Evidence
from app.models.enums import EvidenceType, CryptoPurpose, AssetType

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
        line_number: Optional[int] = None,
        excerpt: Optional[str] = None,
        confidence_score: float = 1.0,
        provenance: Optional[dict] = None,
        algorithm_name: str = "",
        purpose: CryptoPurpose = CryptoPurpose.UNKNOWN,
        asset_type: AssetType = AssetType.API_CALL,
        matched_text: Optional[str] = None,
    ) -> Evidence:
        db_obj = Evidence(
            asset_id=asset_id,
            evidence_type=evidence_type,
            source_file=source_file,
            line_number=line_number,
            detector_name=detector_name,
            detector_version=detector_version,
            excerpt=excerpt,
            provenance=provenance,
            algorithm_name=algorithm_name,
            purpose=purpose,
            asset_type=asset_type,
            matched_text=matched_text,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
# Duplicate block removed

    def get_by_asset(self, asset_id: str) -> List[Evidence]:
        return self.db.query(Evidence).filter(Evidence.asset_id == asset_id).all()
