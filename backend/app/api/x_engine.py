from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.config.domain_baselines import DOMAIN_X_BASELINES, DEFAULT_CONFIDENTIALITY_HORIZON_YEARS
from app.engines.x_engine import XEngine
from app.repositories.project_repository import ProjectRepository
from app.repositories.scan_repository import ScanRepository
from app.models.schemas import XResultResponse, DomainBaselineSchema, XContextUpdateRequest

router = APIRouter(tags=["X Engine — Confidentiality Lifetime"])

@router.get("/x-engine/baselines", response_model=List[DomainBaselineSchema])
def get_domain_baselines():
    """Retrieve research-informed domain baseline configurations for confidentiality planning horizons."""
    return list(DOMAIN_X_BASELINES.values())

@router.post("/x-engine/evaluate", response_model=XResultResponse)
def evaluate_x_context(
    user_x_years: Optional[int] = Query(None),
    user_domain: Optional[str] = Query(None),
    project_name: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    target_path: Optional[str] = Query(None),
    folder_path: Optional[str] = Query(None)
):
    """Standalone X Engine evaluation endpoint for interactive calculation or simulation."""
    engine = XEngine()
    result = engine.evaluate_x(
        user_x_years=user_x_years,
        user_domain=user_domain,
        project_name=project_name,
        description=description,
        target_path=target_path,
        folder_path=folder_path
    )
    return result

@router.get("/projects/{project_id}/x-context", response_model=Dict[str, Any])
def get_project_x_context(project_id: str, folder_path: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Retrieve active X Engine evaluation, domain classification, and folder contexts for a project."""
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    scan_repo = ScanRepository(db)
    scans = scan_repo.get_by_project(project_id)
    latest_scan = scans[-1] if scans else None
    target_path = latest_scan.target_path if latest_scan else None

    engine = XEngine()
    x_result = engine.evaluate_x(
        user_x_years=project.user_x_years,
        user_domain=project.user_domain,
        project_name=project.name,
        description=project.description,
        repository_url=project.repository_url,
        target_path=target_path,
        folder_path=folder_path,
        folder_contexts=project.folder_contexts
    )

    return {
        "project_id": project.id,
        "project_name": project.name,
        "user_x_years": project.user_x_years,
        "user_domain": project.user_domain,
        "folder_contexts": project.folder_contexts or {},
        "x_result": x_result
    }

@router.post("/projects/{project_id}/x-context", response_model=Dict[str, Any])
def update_project_x_context(project_id: str, body: XContextUpdateRequest, db: Session = Depends(get_db)):
    """Update user confidentiality horizon, domain preference, or folder-level overrides for a project."""
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    folder_contexts_update = None
    if body.folder_path and body.folder_x_years is not None:
        folder_contexts_update = {
            body.folder_path.strip("/\\"): {
                "user_x_years": body.folder_x_years,
                "notes": body.folder_notes or "User folder context override"
            }
        }

    updated_project = project_repo.update_x_context(
        project_id=project_id,
        user_x_years=body.user_x_years,
        user_domain=body.user_domain,
        folder_contexts=folder_contexts_update,
        clear_user_x=body.clear_user_x
    )

    scan_repo = ScanRepository(db)
    scans = scan_repo.get_by_project(project_id)
    latest_scan = scans[-1] if scans else None
    target_path = latest_scan.target_path if latest_scan else None

    engine = XEngine()
    x_result = engine.evaluate_x(
        user_x_years=updated_project.user_x_years,
        user_domain=updated_project.user_domain,
        project_name=updated_project.name,
        description=updated_project.description,
        repository_url=updated_project.repository_url,
        target_path=target_path,
        folder_contexts=updated_project.folder_contexts
    )

    return {
        "project_id": updated_project.id,
        "project_name": updated_project.name,
        "user_x_years": updated_project.user_x_years,
        "user_domain": updated_project.user_domain,
        "folder_contexts": updated_project.folder_contexts or {},
        "x_result": x_result
    }
