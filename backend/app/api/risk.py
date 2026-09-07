from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.risk.service import RiskService
from app.models.schemas import RiskAssessRequest

router = APIRouter(tags=["Risk"])

@router.get("/risk", response_model=List[Dict[str, Any]])
def list_risk_assessments(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (CRITICAL, HIGH, MODERATE, LOW)"),
    quantum_status: Optional[str] = Query(None, description="Filter by quantum status"),
    scenario: Optional[str] = Query(None, description="Filter by threat scenario type"),
    minimum_score: Optional[float] = Query(None, description="Filter by minimum risk score"),
    db: Session = Depends(get_db)
):
    """
    List risk assessments with optional filtering.
    """
    service = RiskService(db)
    records = service.risk_repo.list_assessments(
        project_id=project_id,
        risk_level=risk_level,
        quantum_status=quantum_status,
        scenario=scenario,
        minimum_score=minimum_score
    )
    
    asset_repo = AssetRepository(db)
    results = []
    for ra in records:
        asset = asset_repo.get(ra.asset_id)
        threats = service.risk_repo.get_threat_scenarios_for_asset(ra.asset_id)
        results.append(service._assessment_to_dict(ra, asset, threats))

    return results

@router.get("/risk/summary", response_model=Dict[str, Any])
def get_risk_summary(
    project_id: str = Query(..., description="Project ID to summarize"),
    db: Session = Depends(get_db)
):
    """
    Get project-level risk summary, statistics, and deterministic priority list.
    """
    service = RiskService(db)
    return service.get_project_risk_summary(project_id)

@router.get("/risk/{asset_id}", response_model=Dict[str, Any])
def get_asset_risk(
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    Get latest full risk assessment and threat scenarios for a specific asset.
    """
    service = RiskService(db)
    asset = service.asset_repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found.")

    res = service.risk_repo.get_latest_for_asset(asset_id)
    if not res:
        # Trigger assessment on-demand if no assessment exists
        return service.assess_asset(asset_id, force_reassessment=False)

    threats = service.risk_repo.get_threat_scenarios_for_asset(asset_id)
    return service._assessment_to_dict(res, asset, threats)

@router.post("/risk/assess")
def assess_risk(
    req: RiskAssessRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger server-calculated risk assessment for a specific asset or an entire project.
    """
    service = RiskService(db)

    if req.asset_id:
        try:
            return service.assess_asset(
                asset_id=req.asset_id,
                data_sensitivity_label=req.data_sensitivity_label or "UNKNOWN",
                business_criticality_label=req.business_criticality_label or "UNKNOWN",
                data_lifetime_years=req.data_lifetime_years or 10.0,
                migration_time_years=req.migration_time_years or 3.0,
                quantum_threat_horizon_year=req.quantum_threat_horizon_year,
                force_reassessment=req.force_reassessment if req.force_reassessment is not None else True
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    elif req.project_id:
        return service.assess_project(
            project_id=req.project_id,
            data_sensitivity_label=req.data_sensitivity_label or "UNKNOWN",
            business_criticality_label=req.business_criticality_label or "UNKNOWN",
            quantum_threat_horizon_year=req.quantum_threat_horizon_year
        )

    else:
        raise HTTPException(status_code=400, detail="Either 'asset_id' or 'project_id' must be provided in request.")

# Backwards compatible alias routes
@router.post("/projects/{project_id}/risk/assess")
def assess_project_risk_legacy(project_id: str, req: RiskAssessRequest, db: Session = Depends(get_db)):
    service = RiskService(db)
    return service.assess_project(
        project_id=project_id,
        data_sensitivity_label=req.data_sensitivity_label or "UNKNOWN",
        business_criticality_label=req.business_criticality_label or "UNKNOWN",
        quantum_threat_horizon_year=req.quantum_threat_horizon_year
    )

@router.get("/projects/{project_id}/risk/summary")
def get_risk_summary_legacy(project_id: str, db: Session = Depends(get_db)):
    service = RiskService(db)
    return service.get_project_risk_summary(project_id)

@router.get("/assets/{asset_id}/risk")
def get_asset_risk_legacy(asset_id: str, db: Session = Depends(get_db)):
    return get_asset_risk(asset_id=asset_id, db=db)
