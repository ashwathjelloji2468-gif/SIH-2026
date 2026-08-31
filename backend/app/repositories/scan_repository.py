from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.db_models import Scan
from app.models.enums import ScanStatus

class ScanRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, project_id: str, target_path: str, scan_type: str = "source") -> Scan:
        db_obj = Scan(
            project_id=project_id,
            target_path=target_path,
            scan_type=scan_type,
            status=ScanStatus.QUEUED
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get(self, scan_id: str) -> Optional[Scan]:
        return self.db.query(Scan).filter(Scan.id == scan_id).first()

    def get_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[Scan]:
        return self.db.query(Scan).filter(Scan.project_id == project_id).offset(skip).limit(limit).all()

    def update_status(self, scan_id: str, status: ScanStatus, error_message: Optional[str] = None, cbom_json: Optional[dict] = None) -> Optional[Scan]:
        db_obj = self.get(scan_id)
        if not db_obj:
            return None
        db_obj.status = status
        if status in [ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED]:
            db_obj.completed_at = datetime.now(timezone.utc)
        if error_message:
            db_obj.error_message = error_message
        if cbom_json:
            db_obj.cbom_json = cbom_json
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
