from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.repositories.migration_repository import MigrationRepository
from app.repositories.migration_simulation_repository import MigrationSimulationRepository
from app.migration.planner import MigrationPlanner
from app.migration.simulator import MigrationSimulator
from app.migration.sandbox import SandboxEnvironment, SandboxConfig, DEMO_PATTERNS
from app.models.schemas import MigrationPlanCreate, MigrationPlanResponse, MigrationSimulationResponse
from app.models.db_models import MigrationPlan, CryptoAsset
from app.models.enums import SimulationStatus

router = APIRouter(tags=["Migration"])

@router.post("/migration/simulate")
def simulate_asset_migration(
    asset_id: str,
    source_directory: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    simulator = MigrationSimulator()
    try:
        return simulator.run_simulation(db, asset_id=asset_id, source_directory_override=source_directory)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

@router.get("/migration/simulations")
def list_simulations(project_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    repo = MigrationSimulationRepository(db)
    return repo.list_simulations(project_id=project_id)

@router.get("/migration/simulations/{simulation_id}")
def get_simulation(simulation_id: str, db: Session = Depends(get_db)):
    repo = MigrationSimulationRepository(db)
    sim = repo.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail=f"Migration simulation '{simulation_id}' not found.")
    return sim

@router.get("/migration")
def list_all_migration_plans(project_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    repo = MigrationRepository(db)
    if project_id:
        plans = repo.get_plans_by_project(project_id)
    else:
        plans = db.query(MigrationPlan).order_by(MigrationPlan.created_at.desc()).all()
    return plans

@router.get("/migration/summary")
def get_migration_summary(project_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    repo = MigrationRepository(db)
    asset_repo = AssetRepository(db)

    if project_id:
        plans = repo.get_plans_by_project(project_id)
        assets = asset_repo.get_by_project(project_id)
    else:
        plans = db.query(MigrationPlan).all()
        assets = db.query(CryptoAsset).all()

    total_plans = len(plans)
    total_tasks = sum(len(p.tasks) for p in plans)
    total_person_days = sum(p.total_person_days for p in plans)

    task_status_counts = {
        "NOT_STARTED": 0,
        "READY": 0,
        "BLOCKED": 0,
        "IN_PROGRESS": 0,
        "VALIDATION_REQUIRED": 0,
        "COMPLETED": 0
    }

    task_priority_counts = {
        "P0": 0,
        "P1": 0,
        "P2": 0,
        "P3": 0
    }

    for p in plans:
        for t in p.tasks:
            st = getattr(t, "status", "NOT_STARTED")
            if st in task_status_counts:
                task_status_counts[st] += 1
            prio = getattr(t, "priority", "P2")
            if prio in task_priority_counts:
                task_priority_counts[prio] += 1

    return {
        "project_id": project_id,
        "total_migration_plans": total_plans,
        "total_assets_covered": len(assets),
        "total_migration_tasks": total_tasks,
        "total_estimated_person_days": round(total_person_days, 1),
        "task_status_distribution": task_status_counts,
        "task_priority_distribution": task_priority_counts
    }

@router.get("/migration/{asset_id}")
def get_asset_migration_plan(asset_id: str, db: Session = Depends(get_db)):
    planner = MigrationPlanner()
    try:
        return planner.get_asset_migration_summary(db, asset_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/migration/plan")
def create_or_generate_migration_plan(plan_in: MigrationPlanCreate, project_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    target_project_id = project_id
    if not target_project_id:
        first_asset = db.query(CryptoAsset).first()
        if first_asset and first_asset.scan:
            target_project_id = first_asset.scan.project_id
    if not target_project_id:
        raise HTTPException(status_code=400, detail="project_id parameter required to generate migration plan.")
    asset_repo = AssetRepository(db)
    assets = asset_repo.get_by_project(target_project_id)


    planner = MigrationPlanner()
    return planner.create_plan_for_project(
        db=db,
        project_id=target_project_id,
        plan_name=plan_in.name,
        assets=assets,
        vendor_dependency_count=plan_in.vendor_dependency_count or 1,
        pki_cert_dependency_count=plan_in.pki_cert_dependency_count or 1,
        crypto_agility_score=plan_in.crypto_agility_score or 0.6,
        testing_requirement_level=plan_in.testing_requirement_level or "HIGH",
        engineering_capacity_developers=plan_in.engineering_capacity_developers or 3
    )

@router.post("/projects/{project_id}/migration/plans", response_model=MigrationPlanResponse)
def create_project_migration_plan(project_id: str, plan_in: MigrationPlanCreate, db: Session = Depends(get_db)):
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
def simulate_migration_plan(plan_id: str, pattern: Optional[str] = None, db: Session = Depends(get_db)):
    repo = MigrationRepository(db)
    plan = repo.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Migration plan not found")
    
    # Resolve asset to determine dynamic default pattern
    target_asset = None
    if plan.tasks and plan.tasks[0].asset_id:
        target_asset = AssetRepository(db).get(plan.tasks[0].asset_id)
    if not target_asset:
        assets = AssetRepository(db).get_by_project(plan.project_id)
        if assets:
            target_asset = assets[0]

    if not pattern or pattern not in DEMO_PATTERNS:
        if target_asset:
            alg_upper = (target_asset.algorithm_name or "").upper()
            purpose = target_asset.purpose
            if purpose in [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION] or any(k in alg_upper for k in ["ECDSA", "ED25519", "ED448", "DSA"]) or ("RSA" in alg_upper and purpose != CryptoPurpose.KEY_ESTABLISHMENT):
                pattern = "RSA_TO_ML_DSA" if "RSA" in alg_upper else "ECDSA_TO_ML_DSA"
            elif purpose == CryptoPurpose.KEY_ESTABLISHMENT or any(k in alg_upper for k in ["ECDH", "X25519", "X448", "DH", "DIFFIE"]):
                pattern = "ECDH_TO_ML_KEM_HYBRID"
            elif purpose == CryptoPurpose.ENCRYPTION or "AES" in alg_upper:
                pattern = "AES_256_GCM_RETENTION"
            else:
                pattern = "RSA_TO_ML_DSA"
        else:
            pattern = "RSA_TO_ML_DSA"

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

    sim_repo = MigrationSimulationRepository(db)
    asset_id = None
    if plan.tasks and plan.tasks[0].asset_id:
        asset_id = plan.tasks[0].asset_id
    else:
        assets = AssetRepository(db).get_by_project(plan.project_id)
        if assets and assets[0].id:
            asset_id = assets[0].id
        else:
            first_asset = db.query(CryptoAsset).first()
            if first_asset and first_asset.id:
                asset_id = first_asset.id

    if not asset_id:
        raise HTTPException(status_code=400, detail="No cryptographic assets associated with this plan to simulate.")


    result["status"] = "TRANSFORMED"

    sim = sim_repo.create_simulation(
        asset_id=asset_id,
        project_id=plan.project_id,
        migration_plan_id=plan.id,
        sandbox_path=sandbox_dir,
        transformation_type=pattern,
        status=SimulationStatus.TRANSFORMED
    )
    sim_repo.update_simulation_result(
        sim.id,
        status=SimulationStatus.TRANSFORMED,
        changes_summary=result
    )

    return {
        "simulation_id": sim.id,
        "plan_id": plan_id,
        "sandbox_path": sandbox_dir,
        "transformation": result,
        "status": "SIMULATION_COMPLETED"
    }
