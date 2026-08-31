from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.migration_repository import MigrationRepository
from app.validation.test_runner import ValidationEngine
from app.migration.sandbox import SandboxEnvironment
from app.models.schemas import ValidationRunResponse

router = APIRouter(tags=["Validation"])

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

@router.get("/validation/{validation_id}", response_model=ValidationRunResponse)
def get_validation_run(validation_id: str, db: Session = Depends(get_db)):
    repo = MigrationRepository(db)
    val = repo.get_validation_run(validation_id)
    if not val:
        raise HTTPException(status_code=404, detail="Validation run not found")
    return val

@router.get("/validation/{validation_id}/logs")
def get_validation_logs(validation_id: str, db: Session = Depends(get_db)):
    repo = MigrationRepository(db)
    val = repo.get_validation_run(validation_id)
    if not val:
        raise HTTPException(status_code=404, detail="Validation run not found")
    return {"validation_id": validation_id, "logs": val.logs or "No logs available."}
