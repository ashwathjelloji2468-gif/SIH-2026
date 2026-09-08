from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.engines.z_engine import ZEngine, DEFAULT_QUANTUM_HORIZON
from app.repositories.project_repository import ProjectRepository
from app.repositories.asset_repository import AssetRepository
from app.models.schemas import ZResultResponse, ZComponentInput, ZProjectEvaluationResponse

router = APIRouter(tags=["Z Engine — Component-Wise Quantum Exposure"])

@router.post("/z-engine/evaluate-component", response_model=ZResultResponse)
def evaluate_z_component(
    component: ZComponentInput,
    quantum_horizon: Optional[int] = Query(DEFAULT_QUANTUM_HORIZON, ge=1, le=50)
):
    """Evaluate component-wise quantum exposure (Z_i) for a single cryptographic component."""
    engine = ZEngine()
    comp_dict = component.model_dump(exclude_unset=True)
    return engine.evaluate_component(comp_dict, quantum_horizon=quantum_horizon)

@router.get("/projects/{project_id}/z-context", response_model=ZProjectEvaluationResponse)
def get_project_z_context(
    project_id: str,
    quantum_horizon: Optional[int] = Query(DEFAULT_QUANTUM_HORIZON, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Retrieve component-wise Z Engine quantum exposure evaluations for all discovered
    cryptographic artifacts in a project.
    """
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    asset_repo = AssetRepository(db)
    assets = asset_repo.get_by_project(project_id)

    engine = ZEngine()
    return engine.evaluate_project(assets=assets, quantum_horizon=quantum_horizon)

