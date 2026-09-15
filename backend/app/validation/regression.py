import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.enums import ValidationStatus, ValidationCheckType, ValidationCheckStatus
from app.models.db_models import ValidationRun, Project, Scan, MigrationSimulation, MigrationPlan, CryptoAsset
from app.repositories.project_repository import ProjectRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.validation_repository import ValidationRepository
from app.validation.detector import BuildDetector, TestDetector, parse_test_counts
from app.validation.runner import SandboxCommandRunner
from app.migration.sandbox import SandboxEnvironment
from app.migration.transformer import MigrationTransformer

class RegressionAnalyzer:
    """
    Deterministic Before/After Regression Comparison Engine for SENTRIQ (Priority 2 Task #7).
    Compares baseline build & test results against post-migration sandbox build & test results.
    Returns overall classification and transparent human-readable explanations.
    """

    def analyze(
        self,
        before_build: Dict[str, Any],
        before_test: Dict[str, Any],
        after_build: Dict[str, Any],
        after_test: Dict[str, Any],
        migration_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        reasons: List[str] = []

        # 1. Precedence: Migration Failure
        if migration_result and migration_result.get("status") in ["FAILED", "ERROR", "MANUAL_REVIEW_REQUIRED"]:
            mig_err = migration_result.get("error") or migration_result.get("blocker_reason") or "Code transformation failed."
            reasons.append(f"Migration failed before post-migration validation could be executed: {mig_err}")
            return {
                "status": ValidationStatus.MIGRATION_FAILED.value,
                "regression_detected": False,
                "reasons": reasons,
                "before": {"build": before_build, "tests": before_test},
                "after": {"build": {}, "tests": {}}
            }

        # Extract Build Statuses
        b_before_status = str(before_build.get("status", "NOT_CONFIGURED")).upper()
        b_after_status = str(after_build.get("status", "NOT_CONFIGURED")).upper()
        b_before_exit = before_build.get("exit_code", -1)
        b_after_exit = after_build.get("exit_code", -1)

        # Extract Test Statuses
        t_before_status = str(before_test.get("status", "NOT_CONFIGURED")).upper()
        t_after_status = str(after_test.get("status", "NOT_CONFIGURED")).upper()
        t_before_exit = before_test.get("exit_code", -1)
        t_after_exit = after_test.get("exit_code", -1)

        pass_statuses = ["PASSED", "PASS", "SUCCESS"]
        fail_statuses = ["FAILED", "FAIL"]

        build_regression = False
        build_improved = False
        baseline_build_failed = False

        test_regression = False
        test_improved = False
        baseline_tests_failed = False
        count_regression = False

        # 2. Build Regression Rules
        if b_before_status in pass_statuses and b_after_status in fail_statuses:
            build_regression = True
            reasons.append(f"Build changed from PASS to FAIL (exit code {b_after_exit}).")
        elif b_before_status in pass_statuses and b_after_status == "TIMEOUT":
            build_regression = True
            reasons.append("Build changed from PASS to TIMEOUT (process group terminated on timeout).")
        elif b_before_status in pass_statuses and b_after_status == "ERROR":
            build_regression = True
            reasons.append("Build changed from PASS to ERROR.")
        elif b_before_status in fail_statuses and b_after_status in pass_statuses:
            build_improved = True
            reasons.append("Build improved from FAIL to PASS after migration.")
        elif b_before_status in fail_statuses and b_after_status in fail_statuses:
            baseline_build_failed = True
            reasons.append("Baseline build was already failing; after migration it remains failing.")

        # 3. Test Regression Rules
        if t_before_status in pass_statuses and t_after_status in fail_statuses:
            test_regression = True
            reasons.append(f"Unit tests changed from PASS to FAIL (exit code {t_after_exit}).")
        elif t_before_status in pass_statuses and t_after_status == "TIMEOUT":
            test_regression = True
            reasons.append("Unit tests changed from PASS to TIMEOUT (execution timed out).")
        elif t_before_status in pass_statuses and t_after_status == "ERROR":
            test_regression = True
            reasons.append("Unit tests changed from PASS to ERROR.")
        elif t_before_status in fail_statuses and t_after_status in pass_statuses:
            test_improved = True
            reasons.append("Unit tests improved from FAIL to PASS after migration.")
        elif t_before_status in fail_statuses and t_after_status in fail_statuses:
            baseline_tests_failed = True
            reasons.append("Baseline unit tests were already failing; after migration they remain failing.")

        # 4. Count-Based Regression Rules
        tb_passed = before_test.get("tests_passed")
        ta_passed = after_test.get("tests_passed")
        tb_failed = before_test.get("tests_failed")
        ta_failed = after_test.get("tests_failed")

        if (tb_passed is not None and ta_passed is not None) and (tb_failed is not None and ta_failed is not None):
            if ta_passed < tb_passed or ta_failed > tb_failed:
                count_regression = True
                reasons.append(
                    f"Passing unit test count decreased from {tb_passed} to {ta_passed} "
                    f"(failures increased from {tb_failed} to {ta_failed})."
                )

        # 5. Determine Overall Classification
        if build_regression or test_regression or count_regression:
            overall_status = ValidationStatus.REGRESSION.value
            regression_detected = True
        elif baseline_build_failed or baseline_tests_failed:
            overall_status = ValidationStatus.BASELINE_FAILED.value
            regression_detected = False
            if not reasons:
                reasons.append("Baseline build or test execution was failing prior to migration.")
        elif build_improved or test_improved:
            overall_status = ValidationStatus.IMPROVED.value
            regression_detected = False
        elif b_before_status == "NOT_CONFIGURED" and t_before_status == "NOT_CONFIGURED" and b_after_status == "NOT_CONFIGURED" and t_after_status == "NOT_CONFIGURED":
            overall_status = ValidationStatus.NOT_CONFIGURED.value
            regression_detected = False
            reasons.append("No build or test commands configured for baseline or post-migration workspace.")
        elif (b_before_status in pass_statuses or b_before_status == "NOT_CONFIGURED") and \
             (t_before_status in pass_statuses or t_before_status == "NOT_CONFIGURED") and \
             (b_after_status in pass_statuses or b_after_status == "NOT_CONFIGURED") and \
             (t_after_status in pass_statuses or t_after_status == "NOT_CONFIGURED"):
            overall_status = ValidationStatus.NO_REGRESSION.value
            regression_detected = False
            reasons.append("Build and unit tests passed cleanly before and after migration with no regressions detected.")
        else:
            overall_status = ValidationStatus.NO_REGRESSION.value
            regression_detected = False
            reasons.append("No new regressions detected after migration.")

        return {
            "status": overall_status,
            "regression_detected": regression_detected,
            "reasons": reasons,
            "before": {"build": before_build, "tests": before_test},
            "after": {"build": after_build, "tests": after_test}
        }


class RegressionValidationService:
    """
    Orchestrator for Before/After Regression Validation (Priority 2 Task #7).
    REUSES Task #5 BuildDetector and Task #6 TestDetector via SandboxCommandRunner.
    Does NOT instantiate any third command runner.
    """

    def __init__(self, db: Session):
        self.db = db
        self.val_repo = ValidationRepository(db)
        self.proj_repo = ProjectRepository(db)
        self.scan_repo = ScanRepository(db)
        self.build_detector = BuildDetector()
        self.test_detector = TestDetector()
        self.runner = SandboxCommandRunner()
        self.analyzer = RegressionAnalyzer()

    def execute_build_check(self, workspace_dir: str, project_id: str, scan_id: Optional[str] = None) -> Dict[str, Any]:
        dt_started = datetime.now(timezone.utc)
        build_config = self.build_detector.detect_build_config(workspace_dir)
        framework = build_config.get("framework", "Unknown")
        b_status = build_config.get("status", "NOT_SUPPORTED")
        commands = build_config.get("commands", [])

        logs = [f"[BuildSystem] Framework: {framework} (Status: {b_status})"]
        total_duration = 0.0
        total_duration_ms = 0
        is_timeout = False
        last_exit_code = -1
        all_passed = True
        status_val = ValidationStatus.PENDING

        if b_status == "NOT_CONFIGURED":
            status_val = ValidationStatus.NOT_CONFIGURED
            all_passed = False
        elif b_status == "NOT_SUPPORTED":
            status_val = ValidationStatus.NOT_SUPPORTED
            all_passed = False
        elif b_status == "ERROR":
            status_val = ValidationStatus.ERROR
            all_passed = False
        elif b_status == "CONFIGURED" and commands:
            for stage_idx, cmd in enumerate(commands, 1):
                logs.append(f"[BuildCheck] Stage {stage_idx}/{len(commands)}: Executing `{' '.join(cmd)}`")
                chk = self.runner.run_check(workspace_dir, ValidationCheckType.BUILD, cmd, timeout_seconds=30)
                c_stat = chk.get("status")
                total_duration += chk.get("duration", 0.0)
                total_duration_ms += chk.get("duration_ms", 0)
                last_exit_code = chk.get("exit_code", -1)

                if chk.get("timeout"):
                    is_timeout = True
                if chk.get("logs"):
                    logs.append(chk["logs"])

                if c_stat != ValidationCheckStatus.PASS.value:
                    all_passed = False
                    status_val = ValidationStatus.TIMEOUT if is_timeout else ValidationStatus.FAILED
                    break

            if all_passed:
                status_val = ValidationStatus.PASSED
                last_exit_code = 0

        dt_completed = datetime.now(timezone.utc)

        val_run = self.val_repo.create_validation_run(
            project_id=project_id,
            scan_id=scan_id,
            check_type="BUILD",
            status=status_val,
            framework=framework,
            command=" && ".join([" ".join(c) for c in commands]) if commands else None,
            exit_code=last_exit_code if last_exit_code != -1 else (0 if all_passed else 1),
            output_summary=logs[-1] if logs else "",
            duration=round(total_duration, 2),
            duration_ms=total_duration_ms,
            timeout=is_timeout,
            build_passed=all_passed,
            logs="\n".join(logs),
            started_at=dt_started,
            completed_at=dt_completed
        )

        return {
            "validation_id": val_run.id,
            "status": val_run.status.value if hasattr(val_run.status, "value") else str(val_run.status),
            "framework": framework,
            "exit_code": val_run.exit_code,
            "duration": val_run.duration,
            "duration_ms": val_run.duration_ms,
            "timeout": is_timeout,
            "logs": val_run.logs
        }

    def execute_test_check(self, workspace_dir: str, project_id: str, scan_id: Optional[str] = None) -> Dict[str, Any]:
        dt_started = datetime.now(timezone.utc)
        test_config = self.test_detector.detect_test_config(workspace_dir)
        framework = test_config.get("framework", "Unknown")
        t_status = test_config.get("status", "NOT_SUPPORTED")
        commands = test_config.get("commands", [])

        logs = [f"[TestSystem] Framework: {framework} (Status: {t_status})"]
        total_duration = 0.0
        total_duration_ms = 0
        is_timeout = False
        last_exit_code = -1
        all_passed = True
        status_val = ValidationStatus.PENDING
        counts: Dict[str, Optional[int]] = {"total": None, "passed": None, "failed": None, "skipped": None}

        if t_status == "NOT_CONFIGURED":
            status_val = ValidationStatus.NOT_CONFIGURED
            all_passed = False
        elif t_status == "NOT_SUPPORTED":
            status_val = ValidationStatus.NOT_SUPPORTED
            all_passed = False
        elif t_status == "ERROR":
            status_val = ValidationStatus.ERROR
            all_passed = False
        elif t_status == "CONFIGURED" and commands:
            for stage_idx, cmd in enumerate(commands, 1):
                logs.append(f"[TestCheck] Stage {stage_idx}/{len(commands)}: Executing `{' '.join(cmd)}`")
                chk = self.runner.run_check(workspace_dir, ValidationCheckType.UNIT_TEST, cmd, timeout_seconds=60)
                c_stat = chk.get("status")
                total_duration += chk.get("duration", 0.0)
                total_duration_ms += chk.get("duration_ms", 0)
                last_exit_code = chk.get("exit_code", -1)

                if chk.get("timeout"):
                    is_timeout = True
                combined_output = chk.get("logs") or ""
                if combined_output:
                    logs.append(combined_output)
                    counts = parse_test_counts(combined_output)

                if c_stat != ValidationCheckStatus.PASS.value:
                    all_passed = False
                    status_val = ValidationStatus.TIMEOUT if is_timeout else ValidationStatus.FAILED
                    break

            if all_passed:
                status_val = ValidationStatus.PASSED
                last_exit_code = 0

        dt_completed = datetime.now(timezone.utc)

        val_run = self.val_repo.create_validation_run(
            project_id=project_id,
            scan_id=scan_id,
            check_type="UNIT_TEST",
            status=status_val,
            framework=framework,
            command=" && ".join([" ".join(c) for c in commands]) if commands else None,
            exit_code=last_exit_code if last_exit_code != -1 else (0 if all_passed else 1),
            output_summary=logs[-1] if logs else "",
            duration=round(total_duration, 2),
            duration_ms=total_duration_ms,
            timeout=is_timeout,
            unit_tests_passed=all_passed,
            tests_total=counts.get("total"),
            tests_passed=counts.get("passed"),
            tests_failed=counts.get("failed"),
            tests_skipped=counts.get("skipped"),
            logs="\n".join(logs),
            started_at=dt_started,
            completed_at=dt_completed
        )

        return {
            "validation_id": val_run.id,
            "status": val_run.status.value if hasattr(val_run.status, "value") else str(val_run.status),
            "framework": framework,
            "exit_code": val_run.exit_code,
            "duration": val_run.duration,
            "duration_ms": val_run.duration_ms,
            "timeout": is_timeout,
            "tests_total": counts.get("total"),
            "tests_passed": counts.get("passed"),
            "tests_failed": counts.get("failed"),
            "tests_skipped": counts.get("skipped"),
            "logs": val_run.logs
        }

    def run_full_regression_pipeline(
        self,
        project_id: str,
        scan_id: Optional[str] = None,
        simulation_id: Optional[str] = None,
        migration_plan_id: Optional[str] = None,
        asset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        dt_started = datetime.now(timezone.utc)

        proj = self.proj_repo.get(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' not found.")

        target_scan = None
        if scan_id:
            target_scan = self.scan_repo.get(scan_id)
            if not target_scan or target_scan.project_id != project_id:
                raise ValueError(f"Scan '{scan_id}' does not belong to project '{project_id}'.")
        else:
            scans = self.scan_repo.get_by_project(project_id)
            if scans:
                target_scan = scans[0]

        if not target_scan or not target_scan.target_path:
            raise ValueError(f"No scan target path found for project '{project_id}'.")

        original_target_path = target_scan.target_path
        if not os.path.exists(original_target_path):
            raise ValueError(f"Repository source path '{original_target_path}' does not exist on disk.")

        # 1. BEFORE Validation (on untouched original source)
        before_build = self.execute_build_check(original_target_path, project_id, target_scan.id)
        before_test = self.execute_test_check(original_target_path, project_id, target_scan.id)

        # 2. Prepare Sandbox & Apply Migration
        sandbox = None
        sandbox_dir = None
        migration_res = None

        if simulation_id:
            sim = self.db.query(MigrationSimulation).filter(MigrationSimulation.id == simulation_id).first()
            if sim and sim.sandbox_path and os.path.exists(sim.sandbox_path):
                sandbox_dir = sim.sandbox_path
            else:
                import uuid
                sim_id = simulation_id or f"sim_reg_{uuid.uuid4().hex[:8]}"
                sandbox = SandboxEnvironment(simulation_id=sim_id)
                sandbox_dir = sandbox.prepare_sandbox(source_path=original_target_path)
        else:
            import uuid
            temp_sim_id = f"sim_reg_{uuid.uuid4().hex[:8]}"
            sandbox = SandboxEnvironment(simulation_id=temp_sim_id)
            sandbox_dir = sandbox.prepare_sandbox(source_path=original_target_path)

        try:
            if not simulation_id or not (sim and sim.sandbox_path and os.path.exists(sim.sandbox_path)):
                transformer = MigrationTransformer()
                dummy_asset = self.db.query(CryptoAsset).filter(CryptoAsset.scan_id == target_scan.id).first() if not asset_id else self.db.query(CryptoAsset).filter(CryptoAsset.id == asset_id).first()
                if not dummy_asset:
                    dummy_asset = CryptoAsset(id="a_temp", algorithm_name="RSA", location="")

                t_res = transformer.transform_sandbox_code(sandbox_dir, dummy_asset, None)
                if t_res.get("status") in ["FAILED", "MANUAL_REVIEW_REQUIRED"]:
                    migration_res = {"status": "FAILED", "error": t_res.get("changes_summary", {}).get("reason") or "Code transformation failed."}

            if migration_res and migration_res.get("status") == "FAILED":
                analysis = self.analyzer.analyze(before_build, before_test, {}, {}, migration_result=migration_res)
            else:
                # 3. AFTER Validation (on migrated sandbox copy)
                after_build = self.execute_build_check(sandbox_dir, project_id, target_scan.id)
                after_test = self.execute_test_check(sandbox_dir, project_id, target_scan.id)

                # 4. Deterministic Comparison
                analysis = self.analyzer.analyze(before_build, before_test, after_build, after_test)

            dt_completed = datetime.now(timezone.utc)
            val_status = analysis["status"]

            # Persist overall REGRESSION ValidationRun
            val_run = self.val_repo.create_validation_run(
                project_id=project_id,
                scan_id=target_scan.id,
                simulation_id=simulation_id,
                plan_id=migration_plan_id,
                check_type="REGRESSION",
                status=val_status,
                output_summary=analysis["reasons"][0] if analysis["reasons"] else "",
                evidence={
                    "regression_detected": analysis["regression_detected"],
                    "reasons": analysis["reasons"],
                    "before": analysis["before"],
                    "after": analysis["after"]
                },
                duration=round(before_build.get("duration", 0.0) + (analysis["after"].get("build", {}).get("duration", 0.0)), 2),
                logs="\n".join(analysis["reasons"]),
                started_at=dt_started,
                completed_at=dt_completed
            )

            return {
                "id": val_run.id,
                "project_id": project_id,
                "scan_id": target_scan.id,
                "simulation_id": simulation_id,
                "check_type": "REGRESSION",
                "status": val_status,
                "regression_detected": analysis["regression_detected"],
                "reasons": analysis["reasons"],
                "before": analysis["before"],
                "after": analysis["after"],
                "created_at": dt_completed.isoformat()
            }
        finally:
            if sandbox:
                sandbox.cleanup()
