from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.prioritization.service import PrioritizationService
from app.prioritization.schemas import (
    PrioritizationSummaryResponse,
    UserContextUpdateRequest
)

router = APIRouter(tags=["Prioritization"])

@router.get("/prioritization/{project_id}", response_model=PrioritizationSummaryResponse)
def get_project_prioritization(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get ranked, explainable migration prioritization queue (Stage 6) for a project.
    """
    service = PrioritizationService(db)
    return service.get_prioritized_queue(project_id)

@router.post("/prioritization/user-context")
def update_user_context(
    req: UserContextUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update organizational planning preferences (User Focus, User Adjustment) for an asset.
    Preserves original technical risk assessment and system business criticality.
    """
    service = PrioritizationService(db)
    try:
        return service.update_user_context(req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Backward compatible alias route
@router.get("/projects/{project_id}/prioritization", response_model=PrioritizationSummaryResponse)
def get_project_prioritization_legacy(project_id: str, db: Session = Depends(get_db)):
    return get_project_prioritization(project_id=project_id, db=db)
