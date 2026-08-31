from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.repositories.migration_repository import MigrationRepository
from app.migration.planner import MigrationPlanner
from app.migration.sandbox import SandboxEnvironment, SandboxConfig, DEMO_PATTERNS
from app.models.schemas import MigrationPlanCreate, MigrationPlanResponse

router = APIRouter(tags=["Migration"])

@router.post("/projects/{project_id}/migration/plans", response_model=MigrationPlanResponse)
def create_migration_plan(project_id: str, plan_in: MigrationPlanCreate, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    assets = asset_repo.get_by_project(project_id)
    planner = MigrationPlanner()
    return planner.create_plan_for_project(
        db=db,
        project_id=project_id,
        plan_name=plan_in.name,
        assets=assets,
        vendor_dependency_count=plan_in.vendor_dependency_count or 1,
        pki_cert_dependency_count=plan_in.pki_cert_dependency_count or 1,
        crypto_agility_score=plan_in.crypto_agility_score or 0.6,
        testing_requirement_level=plan_in.testing_requirement_level or "HIGH",
        engineering_capacity_developers=plan_in.engineering_capacity_developers or 3
    )

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
def simulate_migration_plan(plan_id: str, pattern: str = "RSA_TO_ML_KEM_HYBRID", db: Session = Depends(get_db)):
    repo = MigrationRepository(db)
    plan = repo.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Migration plan not found")
    
    if pattern not in DEMO_PATTERNS:
        pattern = "RSA_TO_ML_KEM_HYBRID"

    config = SandboxConfig(
        cpu_limit_percent=50,
        memory_limit_mb=512,
        timeout_seconds=60,
        allow_network_access=False,
        requires_human_approval=True
    )
    sandbox = SandboxEnvironment(plan_id, config=config)
    sandbox_dir = sandbox.prepare_sandbox("/tmp/source_demo")
    result = sandbox.apply_transformation_pattern(pattern)

    return {
        "plan_id": plan_id,
        "sandbox_path": sandbox_dir,
        "transformation": result,
        "status": "SIMULATION_COMPLETED"
    }
