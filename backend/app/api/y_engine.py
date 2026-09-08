from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.config.migration_scenarios import MIGRATION_SCENARIOS, DEFAULT_Y_SCENARIO
from app.engines.y_engine import YEngine
from app.repositories.project_repository import ProjectRepository
from app.models.schemas import YResultResponse, MigrationScenarioSchema, YContextUpdateRequest

router = APIRouter(tags=["Y Engine — Migration Time"])

@router.get("/y-engine/scenarios", response_model=List[MigrationScenarioSchema])
def get_migration_scenarios():
    """Retrieve standardized migration planning scenarios (FAST=5y, STANDARD=10y, COMPLEX=15y, LEGACY_HEAVY=20y)."""
    return list(MIGRATION_SCENARIOS.values())

@router.post("/y-engine/evaluate", response_model=YResultResponse)
def evaluate_y_context(user_scenario: Optional[str] = Query(None)):
    """Standalone Y Engine evaluation endpoint for migration planning scenario calculation."""
    engine = YEngine()
    return engine.evaluate_y(user_scenario=user_scenario)

@router.get("/projects/{project_id}/y-context", response_model=Dict[str, Any])
def get_project_y_context(project_id: str, db: Session = Depends(get_db)):
    """Retrieve active Y Engine migration planning evaluation for a project."""
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    engine = YEngine()
    y_result = engine.evaluate_y(user_scenario=project.user_y_scenario)

    return {
        "project_id": project.id,
        "project_name": project.name,
        "user_y_scenario": project.user_y_scenario,
        "y_result": y_result
    }

@router.post("/projects/{project_id}/y-context", response_model=Dict[str, Any])
def update_project_y_context(project_id: str, body: YContextUpdateRequest, db: Session = Depends(get_db)):
    """Update migration planning scenario preference for a project."""
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    updated_project = project_repo.update_y_context(
        project_id=project_id,
        user_y_scenario=body.user_y_scenario,
        clear_user_y=body.clear_user_y
    )

    engine = YEngine()
    y_result = engine.evaluate_y(user_scenario=updated_project.user_y_scenario)

    return {
        "project_id": updated_project.id,
        "project_name": updated_project.name,
        "user_y_scenario": updated_project.user_y_scenario,
        "y_result": y_result
    }
