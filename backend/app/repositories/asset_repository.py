from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.db_models import CryptoAsset
from app.models.enums import AssetType, CryptoPurpose, QuantumSafety

class AssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, scan_id: str, name: str, asset_type: AssetType, algorithm_name: str, location: str, purpose: CryptoPurpose = CryptoPurpose.UNKNOWN, key_size: Optional[int] = None, line_number: Optional[int] = None, quantum_safety: QuantumSafety = QuantumSafety.UNKNOWN) -> CryptoAsset:
        db_obj = CryptoAsset(
            scan_id=scan_id,
            name=name,
            asset_type=asset_type,
            algorithm_name=algorithm_name,
            key_size=key_size,
            purpose=purpose,
            location=location,
            line_number=line_number,
            quantum_safety=quantum_safety
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get(self, asset_id: str) -> Optional[CryptoAsset]:
        return self.db.query(CryptoAsset).filter(CryptoAsset.id == asset_id).first()

    def get_by_scan(self, scan_id: str) -> List[CryptoAsset]:
        return self.db.query(CryptoAsset).filter(CryptoAsset.scan_id == scan_id).all()

    def get_by_project(self, project_id: str) -> List[CryptoAsset]:
        return self.db.query(CryptoAsset).join(CryptoAsset.scan).filter(CryptoAsset.scan.has(project_id=project_id)).all()
