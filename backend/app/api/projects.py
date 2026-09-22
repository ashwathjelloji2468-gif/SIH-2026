from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.project_repository import ProjectRepository
from app.models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    return repo.create(project_in)

@router.get("", response_model=List[ProjectResponse])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    return repo.get_multi(skip=skip, limit=limit)

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    proj = repo.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj

@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, project_in: ProjectUpdate, db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    old_proj = repo.get(project_id)
    old_profile = getattr(old_proj, "default_migration_profile", None) if old_proj else None

    proj = repo.update(project_id, project_in)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    new_profile = getattr(project_in, "default_migration_profile", None)
    if new_profile and new_profile != old_profile:
        from app.repositories.audit_repository import AuditRepository
        AuditRepository(db).log(
            action="MIGRATION_PROFILE_CHANGED",
            actor="system",
            project_id=project_id,
            details={
                "previous_profile": old_profile,
                "new_profile": project_in.default_migration_profile,
                "scope": "PROJECT_DEFAULT"
            }
        )

    if proj:
        from app.context.invalidation import invalidate_project_precomputed_data
        invalidate_project_precomputed_data(project_id, db)
    return proj

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    if not repo.delete(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return None
