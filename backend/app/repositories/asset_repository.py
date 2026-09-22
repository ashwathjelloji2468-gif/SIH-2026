from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from app.models.db_models import CryptoAsset, Scan
from app.models.enums import AssetType, CryptoPurpose, QuantumSafety, ReviewStatus, ScanStatus

class AssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        scan_id: str,
        name: str,
        asset_type: AssetType,
        algorithm_name: str,
        location: str,
        purpose: CryptoPurpose = CryptoPurpose.UNKNOWN,
        key_size: Optional[int] = None,
        line_number: Optional[int] = None,
        quantum_safety: QuantumSafety = QuantumSafety.UNKNOWN,
        is_unknown: bool = False,
        unknown_reason: Optional[str] = None,
        review_status: ReviewStatus = ReviewStatus.RESOLVED,
        extra_metadata: Optional[dict] = None
    ) -> CryptoAsset:
        db_obj = CryptoAsset(
            scan_id=scan_id,
            name=name,
            asset_type=asset_type,
            algorithm_name=algorithm_name,
            key_size=key_size,
            purpose=purpose,
            location=location,
            line_number=line_number,
            quantum_safety=quantum_safety,
            is_unknown=is_unknown,
            unknown_reason=unknown_reason,
            review_status=review_status,
            extra_metadata=extra_metadata
        )

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get(self, asset_id: str) -> Optional[CryptoAsset]:
        return self.db.query(CryptoAsset).options(selectinload(CryptoAsset.evidence_items)).filter(CryptoAsset.id == asset_id).first()

    def get_by_scan(self, scan_id: str) -> List[CryptoAsset]:
        return self.db.query(CryptoAsset).options(selectinload(CryptoAsset.evidence_items)).filter(CryptoAsset.scan_id == scan_id).all()

    def get_by_project(self, project_id: str, scan_id: Optional[str] = None, latest_only: bool = True) -> List[CryptoAsset]:
        if scan_id:
            return (
                self.db.query(CryptoAsset)
                .options(selectinload(CryptoAsset.evidence_items))
                .join(Scan, CryptoAsset.scan_id == Scan.id)
                .filter(CryptoAsset.scan_id == scan_id, Scan.project_id == project_id)
                .all()
            )
        if latest_only:
            latest_scan = (
                self.db.query(Scan)
                .filter(Scan.project_id == project_id, Scan.status == ScanStatus.COMPLETED)
                .order_by(Scan.created_at.desc())
                .first()
            )
            if not latest_scan:
                return []
            return (
                self.db.query(CryptoAsset)
                .options(selectinload(CryptoAsset.evidence_items))
                .filter(CryptoAsset.scan_id == latest_scan.id)
                .all()
            )
        return (
            self.db.query(CryptoAsset)
            .options(selectinload(CryptoAsset.evidence_items))
            .join(Scan, CryptoAsset.scan_id == Scan.id)
            .filter(Scan.project_id == project_id)
            .all()
        )

    def get_unknowns_by_project(self, project_id: str, scan_id: Optional[str] = None, latest_only: bool = True) -> List[CryptoAsset]:
        if scan_id:
            return (
                self.db.query(CryptoAsset)
                .options(selectinload(CryptoAsset.evidence_items))
                .join(Scan, CryptoAsset.scan_id == Scan.id)
                .filter(
                    CryptoAsset.scan_id == scan_id,
                    Scan.project_id == project_id,
                    CryptoAsset.is_unknown == True,
                    CryptoAsset.review_status == ReviewStatus.PENDING_REVIEW
                )
                .all()
            )
        if latest_only:
            latest_scan = (
                self.db.query(Scan)
                .filter(Scan.project_id == project_id, Scan.status == ScanStatus.COMPLETED)
                .order_by(Scan.created_at.desc())
                .first()
            )
            if not latest_scan:
                return []
            return (
                self.db.query(CryptoAsset)
                .options(selectinload(CryptoAsset.evidence_items))
                .filter(
                    CryptoAsset.scan_id == latest_scan.id,
                    CryptoAsset.is_unknown == True,
                    CryptoAsset.review_status == ReviewStatus.PENDING_REVIEW
                )
                .all()
            )
        return (
            self.db.query(CryptoAsset)
            .options(selectinload(CryptoAsset.evidence_items))
            .join(Scan, CryptoAsset.scan_id == Scan.id)
            .filter(
                Scan.project_id == project_id,
                CryptoAsset.is_unknown == True,
                CryptoAsset.review_status == ReviewStatus.PENDING_REVIEW
            )
            .all()
        )

    def review_asset(self, asset_id: str, algorithm_name: Optional[str] = None, purpose: Optional[CryptoPurpose] = None, action: str = "RESOLVE") -> Optional[CryptoAsset]:
        db_obj = self.get(asset_id)
        if not db_obj:
            return None
        if action == "REJECT":
            db_obj.review_status = ReviewStatus.REJECTED
        else:
            db_obj.review_status = ReviewStatus.RESOLVED
            db_obj.is_unknown = False
            if algorithm_name:
                db_obj.algorithm_name = algorithm_name
            if purpose:
                db_obj.purpose = purpose
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
