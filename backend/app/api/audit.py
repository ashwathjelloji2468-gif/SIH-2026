from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.audit_repository import AuditRepository
from app.models.schemas import AuditEventResponse

router = APIRouter(tags=["Audit"])

@router.get("/projects/{project_id}/audit", response_model=List[AuditEventResponse])
def get_project_audit_trail(project_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = AuditRepository(db)
    return repo.get_by_project(project_id, skip=skip, limit=limit)
