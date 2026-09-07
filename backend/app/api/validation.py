from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.migration_repository import MigrationRepository
from app.repositories.migration_simulation_repository import MigrationSimulationRepository
from app.repositories.validation_repository import ValidationRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.validation.validator import MigrationValidator
from app.validation.test_runner import ValidationEngine
from app.migration.sandbox import SandboxEnvironment
from app.models.schemas import ValidationRunResponse
from app.models.db_models import ValidationRun

router = APIRouter(tags=["Validation"])

@router.post("/migration/simulations/{simulation_id}/validate")
def validate_simulation_run(simulation_id: str, db: Session = Depends(get_db)):
    sim_repo = MigrationSimulationRepository(db)
    val_repo = ValidationRepository(db)
    asset_repo = AssetRepository(db)
    rec_repo = RecommendationRepository(db)

    sim = sim_repo.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail=f"Migration simulation '{simulation_id}' not found.")

    asset = asset_repo.get(sim.asset_id)
    rec = rec_repo.get_latest_for_asset(sim.asset_id)

    validator = MigrationValidator()
    val_result = validator.validate_simulation(
        sandbox_dir=sim.sandbox_path or "/tmp",
        transformation_result=sim.changes_summary or {"status": "TRANSFORMED"},
        asset=asset,
        recommendation=rec
    )

    val_run = val_repo.create_validation_run(
        simulation_id=simulation_id,
        asset_id=sim.asset_id,
        check_type="FULL_VALIDATION",
        status=val_result.get("status", "FAILED"),
        build_passed=val_result.get("build_passed", False),
        unit_tests_passed=val_result.get("unit_tests_passed", False),
        crypto_tests_passed=val_result.get("crypto_tests_passed", False),
        integration_tests_passed=val_result.get("integration_tests_passed", False),
        regression_passed=val_result.get("regression_passed", False),
        api_compatible=val_result.get("api_compatible", False),
        logs=val_result.get("logs")
    )

    return val_run

@router.get("/validation/simulation/{simulation_id}")
def get_validation_for_simulation(simulation_id: str, db: Session = Depends(get_db)):
    val_repo = ValidationRepository(db)
    runs = val_repo.get_by_simulation(simulation_id)
    return runs

@router.get("/validation/summary")
def get_validation_summary(db: Session = Depends(get_db)):
    val_repo = ValidationRepository(db)
    runs = val_repo.list_all()

    total_runs = len(runs)
    passed_runs = sum(1 for r in runs if r.status in ["PASS", "PASSED"])
    failed_runs = sum(1 for r in runs if r.status in ["FAIL", "FAILED"])
    blocked_runs = sum(1 for r in runs if r.status in ["BLOCKED", "SKIPPED"])

    return {
        "total_validation_runs": total_runs,
        "passed_runs": passed_runs,
        "failed_runs": failed_runs,
        "blocked_runs": blocked_runs,
        "pass_rate": round(passed_runs / total_runs, 2) if total_runs > 0 else 0.0,
        "runs": runs
    }

@router.post("/migration/plans/{plan_id}/validate", response_model=ValidationRunResponse)
def validate_migration_plan(plan_id: str, db: Session = Depends(get_db)):
    repo = MigrationRepository(db)
    plan = repo.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Migration plan not found")
    
    sandbox = SandboxEnvironment(plan_id)
    sandbox_dir = sandbox.prepare_sandbox("/tmp/source_demo")
    
    validator = ValidationEngine()
    result = validator.run_validation(sandbox_dir)

    val_run = repo.create_validation_run(
        plan_id=plan_id,
        status=result["status"],
        build_passed=result["build_passed"],
        unit_tests_passed=result["unit_tests_passed"],
        crypto_tests_passed=result["crypto_tests_passed"],
        logs=result["logs"]
    )
    return val_run

@router.get("/validation/{validation_id}")
def get_validation_run(validation_id: str, db: Session = Depends(get_db)):
    val_repo = ValidationRepository(db)
    val = val_repo.get(validation_id)
    if not val:
        repo = MigrationRepository(db)
        val = repo.get_validation_run(validation_id)
    if not val:
        raise HTTPException(status_code=404, detail="Validation run not found")
    return val

@router.get("/validation/{validation_id}/logs")
def get_validation_logs(validation_id: str, db: Session = Depends(get_db)):
    val_repo = ValidationRepository(db)
    val = val_repo.get(validation_id)
    if not val:
        repo = MigrationRepository(db)
        val = repo.get_validation_run(validation_id)
    if not val:
        raise HTTPException(status_code=404, detail="Validation run not found")
    return {"validation_id": validation_id, "logs": val.logs or "No logs available."}
