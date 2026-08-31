from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.db_models import AuditEvent

class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(self, action: str, actor: str = "system", project_id: Optional[str] = None, details: Optional[dict] = None) -> AuditEvent:
        event = AuditEvent(
            action=action,
            actor=actor,
            project_id=project_id,
            details=details or {}
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[AuditEvent]:
        return self.db.query(AuditEvent).filter(AuditEvent.project_id == project_id).offset(skip).limit(limit).all()
