from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.business_criticality_service import BusinessCriticalityService

router = APIRouter(tags=["Business Criticality"])

class UpdateBusinessCriticalityRequest(BaseModel):
    factor_ratings: Optional[Dict[str, int]] = Field(None, description="Updated factor rating values (0 to 5)")
    user_override: Optional[str] = Field(None, description="Planning criticality override (LOW, MEDIUM, HIGH, CRITICAL)")
    adjustment_reason: Optional[str] = Field(None, description="Non-empty reason required when setting override")
    revert_override: Optional[bool] = Field(False, description="Revert override back to system classification")

class OverrideBusinessCriticalityRequest(BaseModel):
    user_override: str = Field(..., description="Planning criticality override (LOW, MEDIUM, HIGH, CRITICAL)")
    adjustment_reason: str = Field(..., description="Non-empty reason required for override")

@router.get("/projects/{project_id}/business-criticality")
def get_project_business_criticality(project_id: str, db: Session = Depends(get_db)):
    service = BusinessCriticalityService(db)
    try:
        return service.get_project_business_criticality(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/projects/{project_id}/business-criticality")
def update_project_business_criticality(
    project_id: str,
    req: UpdateBusinessCriticalityRequest,
    db: Session = Depends(get_db)
):
    service = BusinessCriticalityService(db)
    try:
        return service.update_project_business_criticality(
            project_id=project_id,
            factor_ratings=req.factor_ratings,
            user_override=req.user_override,
            adjustment_reason=req.adjustment_reason,
            revert_override=req.revert_override or False
        )
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=404, detail=err_msg)
        else:
            raise HTTPException(status_code=422, detail=err_msg)

@router.post("/projects/{project_id}/business-criticality/override")
def override_project_business_criticality(
    project_id: str,
    req: OverrideBusinessCriticalityRequest,
    db: Session = Depends(get_db)
):
    service = BusinessCriticalityService(db)
    try:
        return service.update_project_business_criticality(
            project_id=project_id,
            user_override=req.user_override,
            adjustment_reason=req.adjustment_reason,
            revert_override=False
        )
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=404, detail=err_msg)
        else:
            raise HTTPException(status_code=422, detail=err_msg)

@router.post("/projects/{project_id}/business-criticality/revert")
def revert_project_business_criticality(
    project_id: str,
    db: Session = Depends(get_db)
):
    service = BusinessCriticalityService(db)
    try:
        return service.update_project_business_criticality(
            project_id=project_id,
            revert_override=True
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
