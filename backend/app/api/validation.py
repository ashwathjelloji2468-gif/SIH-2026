import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.migration_repository import MigrationRepository
from app.repositories.migration_simulation_repository import MigrationSimulationRepository
from app.repositories.validation_repository import ValidationRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.scan_repository import ScanRepository
from app.validation.validator import MigrationValidator
from app.validation.test_runner import ValidationEngine
from app.validation.detector import BuildDetector, TestDetector, parse_test_counts
from app.validation.runner import SandboxCommandRunner
from app.migration.sandbox import SandboxEnvironment
from app.models.schemas import ValidationRunResponse
from app.models.db_models import ValidationRun
from app.models.enums import ValidationStatus, ValidationCheckStatus, ValidationCheckType

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
        status=val_result.get("status", "PASSED"),
        build_passed=val_result.get("build_passed", True),
        unit_tests_passed=val_result.get("unit_tests_passed", True),
        crypto_tests_passed=val_result.get("crypto_tests_passed", True),
        integration_tests_passed=val_result.get("integration_tests_passed", True),
        regression_passed=val_result.get("regression_passed", True),
        api_compatible=val_result.get("api_compatible", True),
        logs=val_result.get("logs"),
        residual_risk_score=val_result.get("residual_risk_score", 15.0),
        confidence=val_result.get("confidence", 0.92)
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

@router.post("/projects/{project_id}/validation/build", response_model=ValidationRunResponse)
def execute_project_build_validation(
    project_id: str,
    scan_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    dt_started = datetime.now(timezone.utc)
    proj_repo = ProjectRepository(db)
    scan_repo = ScanRepository(db)
    val_repo = ValidationRepository(db)

    proj = proj_repo.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    target_scan = None
    if scan_id:
        target_scan = scan_repo.get(scan_id)
        if not target_scan or target_scan.project_id != project_id:
            raise HTTPException(status_code=400, detail=f"Scan '{scan_id}' does not belong to project '{project_id}'.")
    else:
        scans = scan_repo.get_by_project(project_id)
        if scans:
            target_scan = scans[0]

    if not target_scan or not target_scan.target_path:
        raise HTTPException(status_code=409, detail=f"No scan target path found for project '{project_id}'.")

    target_path = target_scan.target_path
    if not os.path.exists(target_path):
        raise HTTPException(status_code=409, detail=f"Repository source path '{target_path}' does not exist on disk.")

    detector = BuildDetector()
    runner = SandboxCommandRunner()

    build_config = detector.detect_build_config(target_path)
    framework = build_config.get("framework", "Unknown")
    b_status = build_config.get("status", "NOT_SUPPORTED")
    commands = build_config.get("commands", [])

    logs = [f"[BuildSystem] Discovered Framework: {framework} (Status: {b_status})"]
    total_duration = 0.0
    total_duration_ms = 0
    is_timeout = False
    last_exit_code = -1
    all_passed = True
    executed_command = None
    status_val = ValidationStatus.PENDING

    if b_status == "NOT_CONFIGURED":
        status_val = ValidationStatus.NOT_CONFIGURED
        logs.append(f"[BuildCheck] Status: NOT_CONFIGURED — {build_config.get('details')}")
        all_passed = False
    elif b_status == "NOT_SUPPORTED":
        status_val = ValidationStatus.NOT_SUPPORTED
        logs.append(f"[BuildCheck] Status: NOT_SUPPORTED — {build_config.get('details')}")
        all_passed = False
    elif b_status == "ERROR":
        status_val = ValidationStatus.ERROR
        logs.append(f"[BuildCheck] Status: ERROR — {build_config.get('details')}")
        all_passed = False
    elif b_status == "CONFIGURED" and commands:
        executed_command = " && ".join([" ".join(c) for c in commands])
        for stage_idx, cmd in enumerate(commands, 1):
            logs.append(f"[BuildCheck] Stage {stage_idx}/{len(commands)}: Executing command `{' '.join(cmd)}`")
            chk = runner.run_check(target_path, ValidationCheckType.BUILD, cmd, timeout_seconds=30)

            c_stat = chk.get("status")
            total_duration += chk.get("duration", 0.0)
            total_duration_ms += chk.get("duration_ms", 0)
            last_exit_code = chk.get("exit_code", -1)

            if chk.get("timeout"):
                is_timeout = True

            if chk.get("logs"):
                logs.append(f"--- Stage {stage_idx} Command Output ---\n{chk['logs']}")

            if c_stat != ValidationCheckStatus.PASS.value:
                all_passed = False
                if is_timeout:
                    status_val = ValidationStatus.TIMEOUT
                else:
                    status_val = ValidationStatus.FAILED
                logs.append(f"[BuildCheck] Stage {stage_idx} Failed with status: {c_stat} (exit code {last_exit_code})")
                break

        if all_passed:
            status_val = ValidationStatus.PASSED
            last_exit_code = 0
            logs.append("[BuildCheck] Status: PASS — All build stages completed successfully.")

    dt_completed = datetime.now(timezone.utc)

    val_run = val_repo.create_validation_run(
        project_id=project_id,
        scan_id=target_scan.id,
        check_type="BUILD",
        status=status_val,
        framework=framework,
        command=executed_command,
        exit_code=last_exit_code if last_exit_code != -1 else (0 if all_passed else 1),
        output_summary=logs[-1] if logs else "",
        evidence={"framework": framework, "build_config": build_config},
        duration=round(total_duration, 2),
        duration_ms=total_duration_ms,
        timeout=is_timeout,
        build_passed=all_passed,
        logs="\n".join(logs),
        residual_risk_score=15.0 if all_passed else 65.0,
        confidence=0.92 if all_passed else 0.40,
        started_at=dt_started,
        completed_at=dt_completed
    )

    return val_run

@router.post("/projects/{project_id}/validation/tests", response_model=ValidationRunResponse)
def execute_project_test_validation(
    project_id: str,
    scan_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    dt_started = datetime.now(timezone.utc)
    proj_repo = ProjectRepository(db)
    scan_repo = ScanRepository(db)
    val_repo = ValidationRepository(db)

    proj = proj_repo.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    target_scan = None
    if scan_id:
        target_scan = scan_repo.get(scan_id)
        if not target_scan or target_scan.project_id != project_id:
            raise HTTPException(status_code=400, detail=f"Scan '{scan_id}' does not belong to project '{project_id}'.")
    else:
        scans = scan_repo.get_by_project(project_id)
        if scans:
            target_scan = scans[0]

    if not target_scan or not target_scan.target_path:
        raise HTTPException(status_code=409, detail=f"No scan target path found for project '{project_id}'.")

    target_path = target_scan.target_path
    if not os.path.exists(target_path):
        raise HTTPException(status_code=409, detail=f"Repository source path '{target_path}' does not exist on disk.")

    detector = TestDetector()
    runner = SandboxCommandRunner()

    test_config = detector.detect_test_config(target_path)
    framework = test_config.get("framework", "Unknown")
    t_status = test_config.get("status", "NOT_SUPPORTED")
    commands = test_config.get("commands", [])

    logs = [f"[TestSystem] Discovered Framework: {framework} (Status: {t_status})"]
    total_duration = 0.0
    total_duration_ms = 0
    is_timeout = False
    last_exit_code = -1
    all_passed = True
    executed_command = None
    status_val = ValidationStatus.PENDING
    counts: Dict[str, Optional[int]] = {"total": None, "passed": None, "failed": None, "skipped": None}

    if t_status == "NOT_CONFIGURED":
        status_val = ValidationStatus.NOT_CONFIGURED
        logs.append(f"[TestCheck] Status: NOT_CONFIGURED — {test_config.get('details')}")
        all_passed = False
    elif t_status == "NOT_SUPPORTED":
        status_val = ValidationStatus.NOT_SUPPORTED
        logs.append(f"[TestCheck] Status: NOT_SUPPORTED — {test_config.get('details')}")
        all_passed = False
    elif t_status == "ERROR":
        status_val = ValidationStatus.ERROR
        logs.append(f"[TestCheck] Status: ERROR — {test_config.get('details')}")
        all_passed = False
    elif t_status == "CONFIGURED" and commands:
        executed_command = " && ".join([" ".join(c) for c in commands])
        for stage_idx, cmd in enumerate(commands, 1):
            logs.append(f"[TestCheck] Stage {stage_idx}/{len(commands)}: Executing test command `{' '.join(cmd)}`")
            chk = runner.run_check(target_path, ValidationCheckType.UNIT_TEST, cmd, timeout_seconds=60)

            c_stat = chk.get("status")
            total_duration += chk.get("duration", 0.0)
            total_duration_ms += chk.get("duration_ms", 0)
            last_exit_code = chk.get("exit_code", -1)

            if chk.get("timeout"):
                is_timeout = True

            combined_output = (chk.get("logs") or "")
            if combined_output:
                logs.append(f"--- Stage {stage_idx} Test Output ---\n{combined_output}")
                counts = parse_test_counts(combined_output)

            if c_stat != ValidationCheckStatus.PASS.value:
                all_passed = False
                if is_timeout:
                    status_val = ValidationStatus.TIMEOUT
                else:
                    status_val = ValidationStatus.FAILED
                logs.append(f"[TestCheck] Stage {stage_idx} Failed with status: {c_stat} (exit code {last_exit_code})")
                break

        if all_passed:
            status_val = ValidationStatus.PASSED
            last_exit_code = 0
            logs.append("[TestCheck] Status: PASS — All unit test commands executed successfully.")

    dt_completed = datetime.now(timezone.utc)

    val_run = val_repo.create_validation_run(
        project_id=project_id,
        scan_id=target_scan.id,
        check_type="UNIT_TEST",
        status=status_val,
        framework=framework,
        command=executed_command,
        exit_code=last_exit_code if last_exit_code != -1 else (0 if all_passed else 1),
        output_summary=logs[-1] if logs else "",
        evidence={"framework": framework, "test_config": test_config, "test_counts": counts},
        duration=round(total_duration, 2),
        duration_ms=total_duration_ms,
        timeout=is_timeout,
        unit_tests_passed=all_passed,
        tests_total=counts.get("total"),
        tests_passed=counts.get("passed"),
        tests_failed=counts.get("failed"),
        tests_skipped=counts.get("skipped"),
        logs="\n".join(logs),
        residual_risk_score=15.0 if all_passed else 65.0,
        confidence=0.92 if all_passed else 0.40,
        started_at=dt_started,
        completed_at=dt_completed
    )

    return val_run

@router.post("/projects/{project_id}/validation/regression")
def execute_project_regression_validation(
    project_id: str,
    scan_id: Optional[str] = Query(None),
    simulation_id: Optional[str] = Query(None),
    migration_plan_id: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    from app.validation.regression import RegressionValidationService
    service = RegressionValidationService(db)
    try:
        res = service.run_full_regression_pipeline(
            project_id=project_id,
            scan_id=scan_id,
            simulation_id=simulation_id,
            migration_plan_id=migration_plan_id,
            asset_id=asset_id
        )
        return res
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=404, detail=err_msg)
        elif "does not belong" in err_msg.lower():
            raise HTTPException(status_code=400, detail=err_msg)
        else:
            raise HTTPException(status_code=409, detail=err_msg)

@router.post("/migration/plans/{plan_id}/validate", response_model=ValidationRunResponse)
def validate_migration_plan(plan_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import desc
    from app.models.db_models import MigrationSimulation

    repo = MigrationRepository(db)
    plan = repo.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Migration plan not found")

    sim = db.query(MigrationSimulation).filter(MigrationSimulation.migration_plan_id == plan_id).order_by(desc(MigrationSimulation.created_at)).first()

    if not sim:
        raise HTTPException(status_code=409, detail="No valid simulation sandbox workspace found for this plan. Please run Stage 2 simulation first.")

    sandbox_dir = sim.sandbox_path if (sim.sandbox_path and os.path.exists(sim.sandbox_path)) else "/tmp"
    transformation_type = sim.transformation_type or ""
    validator = ValidationEngine()
    result = validator.run_validation(
        sandbox_path=sandbox_dir,
        transformation_type=transformation_type,
        target_candidate=""
    )

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
