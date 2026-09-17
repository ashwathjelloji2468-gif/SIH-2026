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
        raise HTTPException(status_code=400, detail="project_id parameter required to generate migration plan.")
    asset_repo = AssetRepository(db)
    assets = asset_repo.get_by_project(target_project_id)

    planner = MigrationPlanner()
    plan = planner.create_plan_for_project(
        db=db,
        project_id=target_project_id,
        plan_name=plan_in.name,
        assets=assets,
        vendor_dependency_count=plan_in.vendor_dependency_count or 1,
        pki_cert_dependency_count=plan_in.pki_cert_dependency_count or 1,
        crypto_agility_score=plan_in.crypto_agility_score or 0.6,
        testing_requirement_level=plan_in.testing_requirement_level or "HIGH",
        engineering_capacity_developers=plan_in.engineering_capacity_developers or 3,
        profile=plan_in.profile
    )
    if plan_in.profile:
        from app.repositories.audit_repository import AuditRepository
        AuditRepository(db).log(
            action="MIGRATION_PROFILE_CHANGED",
            actor="system",
            project_id=target_project_id,
            details={"plan_id": plan.id, "new_profile": plan.profile, "scope": "MIGRATION_PLAN"}
        )
    return plan

@router.post("/projects/{project_id}/migration/plans", response_model=MigrationPlanResponse)
def create_project_migration_plan(project_id: str, plan_in: MigrationPlanCreate, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    assets = asset_repo.get_by_project(project_id)
    planner = MigrationPlanner()
    plan = planner.create_plan_for_project(
        db=db,
        project_id=project_id,
        plan_name=plan_in.name,
        assets=assets,
        vendor_dependency_count=plan_in.vendor_dependency_count or 1,
        pki_cert_dependency_count=plan_in.pki_cert_dependency_count or 1,
        crypto_agility_score=plan_in.crypto_agility_score or 0.6,
        testing_requirement_level=plan_in.testing_requirement_level or "HIGH",
        engineering_capacity_developers=plan_in.engineering_capacity_developers or 3,
        profile=plan_in.profile
    )
    if plan_in.profile:
        from app.repositories.audit_repository import AuditRepository
        AuditRepository(db).log(
            action="MIGRATION_PROFILE_CHANGED",
            actor="system",
            project_id=project_id,
            details={"plan_id": plan.id, "new_profile": plan.profile, "scope": "MIGRATION_PLAN"}
        )
    return plan

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
def recalculate_migration_plan(plan_id: str, profile: Optional[str] = Query(None), db: Session = Depends(get_db)):
    repo = MigrationRepository(db)
    plan = repo.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Migration plan not found")
    if profile:
        raw_prof = str(profile).upper()
        if raw_prof in ["LOW_LATENCY", "BALANCED", "SECURITY_FIRST"] and raw_prof != plan.profile:
            old_prof = plan.profile
            plan.profile = raw_prof
            from app.repositories.audit_repository import AuditRepository
            AuditRepository(db).log(
                action="MIGRATION_PROFILE_CHANGED",
                actor="system",
                project_id=plan.project_id,
                details={"plan_id": plan.id, "previous_profile": old_prof, "new_profile": raw_prof, "scope": "MIGRATION_PLAN"}
            )
            # Re-estimate effort with new profile
            assets = AssetRepository(db).get_by_project(plan.project_id)
            distinct_files = len(set(a.location for a in assets if getattr(a, "location", None)))
            from app.migration.effort_estimator import estimate_migration_effort
            effort = estimate_migration_effort(
                affected_assets_count=len(assets),
                affected_files_count=distinct_files,
                blast_radius_affected_nodes=len(assets),
                business_criticality_score=75.0
            )
            plan.effort_level = effort["effort_level"]
            plan.effort_factors = effort.get("factors", [])
            plan.total_person_days = effort["person_days"]
            plan.total_calendar_months = effort["calendar_months"]
            plan.assumptions = effort["assumptions"]
            db.commit()
            db.refresh(plan)
    return plan

@router.post("/migration/plans/{plan_id}/simulate")
def simulate_migration_plan(
    plan_id: str,
    pattern: Optional[str] = None,
    asset_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    repo = MigrationRepository(db)
    plan = repo.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Migration plan not found.")

    target_asset = None
    if asset_id:
        target_asset = AssetRepository(db).get(asset_id)
        if not target_asset:
            raise HTTPException(status_code=404, detail=f"Cryptographic asset '{asset_id}' not found.")
        
        # Verify that the asset belongs to the requested migration plan
        plan_asset_ids = set()
        if plan.tasks:
            plan_asset_ids = {t.asset_id for t in plan.tasks if t.asset_id}
        if not plan_asset_ids:
            project_assets = AssetRepository(db).get_by_project(plan.project_id)
            plan_asset_ids = {a.id for a in project_assets}

        if target_asset.id not in plan_asset_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Asset '{asset_id}' does not belong to migration plan '{plan_id}'."
            )
    else:
        if plan.tasks and plan.tasks[0].asset_id:
            target_asset = AssetRepository(db).get(plan.tasks[0].asset_id)
        if not target_asset:
            assets = AssetRepository(db).get_by_project(plan.project_id)
            if assets:
                target_asset = assets[0]

    if not target_asset:
        raise HTTPException(
            status_code=409,
            detail="Migration cannot be simulated because no cryptographic assets belong to this project/plan.",
        )

    simulator = MigrationSimulator()
    try:
        sim_res = simulator.run_simulation(db, asset_id=target_asset.id, migration_plan_id=plan_id, requested_pattern=pattern)
        if sim_res.get("status") == "BLOCKED":
            blocker = sim_res.get("blocker_reason") or "Migration source repository path does not exist on disk or is unavailable."
            raise HTTPException(status_code=409, detail=f"Migration cannot start: {blocker}")
        return {
            "simulation_id": sim_res["simulation_id"],
            "plan_id": plan_id,
            "sandbox_path": sim_res.get("sandbox_path", ""),
            "transformation": sim_res,
            "status": "SIMULATION_COMPLETED",
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=409, detail=f"Migration cannot start: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation execution error: {str(e)}")
