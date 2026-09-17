from typing import List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.db_models import Scan
from app.models.enums import ScanStatus

STALE_THRESHOLD_MINUTES = 30
STALE_ERROR_MESSAGE = "Scan execution became stale and was automatically reconciled after exceeding the 30-minute execution window."

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

    def reconcile_stale_scans(self, project_id: Optional[str] = None) -> List[Scan]:
        now = datetime.now(timezone.utc)
        threshold_time = now - timedelta(minutes=STALE_THRESHOLD_MINUTES)

        query = self.db.query(Scan).filter(Scan.status == ScanStatus.RUNNING)
        if project_id:
            query = query.filter(Scan.project_id == project_id)

        running_scans = query.all()
        reconciled = []

        for scan in running_scans:
            created_at = scan.created_at
            if created_at is not None:
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if created_at < threshold_time:
                    self.update_status(
                        scan_id=scan.id,
                        status=ScanStatus.FAILED,
                        error_message=STALE_ERROR_MESSAGE
                    )
                    reconciled.append(scan)

        return reconciled

    def get_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[Scan]:
        self.reconcile_stale_scans(project_id)
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
