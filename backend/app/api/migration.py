from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.repositories.migration_repository import MigrationRepository
from app.migration.planner import MigrationPlanner
from app.migration.sandbox import SandboxEnvironment
from app.models.schemas import MigrationPlanCreate, MigrationPlanResponse

router = APIRouter(tags=["Migration"])

@router.post("/projects/{project_id}/migration/plans", response_model=MigrationPlanResponse)
def create_migration_plan(project_id: str, plan_in: MigrationPlanCreate, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    assets = asset_repo.get_by_project(project_id)
    planner = MigrationPlanner()
    return planner.create_plan_for_project(db, project_id, plan_in.name, assets)

@router.get("/projects/{project_id}/migration/plans", response_model=List[MigrationPlanResponse])
def list_migration_plans(project_id: str, db: Session = Depends(get_db)):
    repo = MigrationRepository(db)
    return repo.get_plans_by_project(project_id)

@router.get("/migration/plans/{plan_id}", response_model=MigrationPlanResponse)
def get_migration_plan(plan_id: str, db: Session = Depends(get_db)):
    repo = MigrationRepository(db)
    plan = repo.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Migration plan not found")
    return plan

@router.post("/migration/plans/{plan_id}/recalculate", response_model=MigrationPlanResponse)
def recalculate_migration_plan(plan_id: str, db: Session = Depends(get_db)):
    repo = MigrationRepository(db)
    plan = repo.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Migration plan not found")
    return plan

@router.post("/migration/plans/{plan_id}/simulate")
def simulate_migration_plan(plan_id: str, db: Session = Depends(get_db)):
    repo = MigrationRepository(db)
    plan = repo.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Migration plan not found")
    
    sandbox = SandboxEnvironment(plan_id)
    sandbox_dir = sandbox.prepare_sandbox("/tmp/source_demo")
    patch_applied = sandbox.apply_patch("demo_patch")

    return {
        "plan_id": plan_id,
        "sandbox_path": sandbox_dir,
        "patch_applied": patch_applied,
        "status": "SIMULATION_COMPLETED"
    }
