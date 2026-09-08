from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.engines.mosca_engine import MoscaEngine
from app.repositories.project_repository import ProjectRepository
from app.repositories.asset_repository import AssetRepository
from app.models.schemas import MoscaComponentResultResponse, MoscaProjectEvaluationResponse, ZComponentInput

router = APIRouter(tags=["Mosca Engine — Integrated X + Y - Z"])

@router.post("/mosca/evaluate-component", response_model=MoscaComponentResultResponse)
def evaluate_mosca_component(
    component: ZComponentInput,
    user_x_years: Optional[int] = Query(None),
    user_domain: Optional[str] = Query(None),
    user_y_scenario: Optional[str] = Query(None),
    quantum_horizon: Optional[int] = Query(None)
):
    """Evaluate component-wise Mosca risk (M_i = X + Y - Z_i) for a single cryptographic component."""
    engine = MoscaEngine()
    comp_dict = component.model_dump(exclude_unset=True)
    return engine.evaluate_component_mosca(
        component=comp_dict,
        user_x_years=user_x_years,
        user_domain=user_domain,
        user_y_scenario=user_y_scenario,
        quantum_horizon=quantum_horizon
    )

@router.get("/projects/{project_id}/mosca-context", response_model=MoscaProjectEvaluationResponse)
def get_project_mosca_context(
    project_id: str,
    quantum_horizon: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retrieve integrated component-wise Mosca Engine evaluations (M_i = X + Y - Z_i)
    for all discovered cryptographic artifacts in a project.
    """
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    asset_repo = AssetRepository(db)
    assets = asset_repo.get_by_project(project_id)

    engine = MoscaEngine()
    return engine.evaluate_project_mosca(
        project=project,
        assets=assets,
        quantum_horizon=quantum_horizon
    )
