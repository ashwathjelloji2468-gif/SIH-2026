from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.audit_repository import AuditRepository
from app.models.schemas import AuditEventResponse

router = APIRouter(tags=["Audit"])

from pydantic import BaseModel
from app.audit import get_audit_provider, AuditResult

class AuditVerifyRequest(BaseModel):
    artifact_type: str
    artifact_id: str
    digest: str

@router.get("/projects/{project_id}/audit", response_model=List[AuditEventResponse])
def get_project_audit_trail(project_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = AuditRepository(db)
    return repo.get_by_project(project_id, skip=skip, limit=limit)

@router.post("/audit/verify", response_model=AuditResult)
def verify_audit_digest(request: AuditVerifyRequest):
    provider = get_audit_provider()
    return provider.verify_artifact_digest(
        artifact_type=request.artifact_type,
        artifact_id=request.artifact_id,
        digest=request.digest
    )
