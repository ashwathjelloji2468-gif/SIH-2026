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
    plan_repo = MigrationRepository(db)

    sim = sim_repo.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail=f"Migration simulation '{simulation_id}' not found.")

    if sim.migration_plan_id:
        plan = plan_repo.get_plan(sim.migration_plan_id)
        if not plan:
            raise HTTPException(status_code=409, detail="Migration simulation references a migration plan that does not exist.")

    asset = asset_repo.get(sim.asset_id) if sim.asset_id else None
    rec = rec_repo.get_latest_for_asset(sim.asset_id) if sim.asset_id else None

    validator = MigrationValidator()
    val_result = validator.validate_simulation(
        sandbox_dir=sim.sandbox_path or "/tmp",
        transformation_result=sim.changes_summary or {"status": "TRANSFORMED"},
        asset=asset,
        recommendation=rec
    )

    val_run = val_repo.create_validation_run(
        simulation_id=simulation_id,
        plan_id=sim.migration_plan_id,
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
def get_validation_summary(project_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    val_repo = ValidationRepository(db)
    runs = val_repo.get_by_project(project_id) if project_id else val_repo.list_all()

    total_runs = len(runs)
    passed_runs = sum(1 for r in runs if getattr(r.status, "value", str(r.status)) in ["PASS", "PASSED", "SUCCESS"])
    failed_runs = sum(1 for r in runs if getattr(r.status, "value", str(r.status)) in ["FAIL", "FAILED"])
    error_runs = sum(1 for r in runs if getattr(r.status, "value", str(r.status)) in ["ERROR", "BLOCKED"])
    in_progress_runs = sum(1 for r in runs if getattr(r.status, "value", str(r.status)) in ["PENDING", "IN_PROGRESS", "RUNNING"])

    avg_conf = (sum(r.confidence for r in runs if r.confidence is not None) / total_runs) if total_runs > 0 else 0.0
    avg_risk = (sum(r.residual_risk_score for r in runs if r.residual_risk_score is not None) / total_runs) if total_runs > 0 else 0.0

    return {
        "total_validations": total_runs,
        "passed": passed_runs,
        "failed": failed_runs,
        "error": error_runs,
        "in_progress": in_progress_runs,
        "average_confidence": round(avg_conf, 2),
        "average_residual_risk": round(avg_risk, 1),
        "total_validation_runs": total_runs,
        "passed_runs": passed_runs,
        "failed_runs": failed_runs,
        "blocked_runs": error_runs,
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
