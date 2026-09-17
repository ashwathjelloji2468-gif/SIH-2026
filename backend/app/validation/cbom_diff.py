import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.db_models import Project, Scan, ValidationRun, MigrationSimulation, CryptoAsset
from app.models.enums import ScanStatus, ValidationStatus
from app.repositories.project_repository import ProjectRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.validation_repository import ValidationRepository
from app.orchestration.scan_orchestrator import ScanOrchestrator
from app.cbom.comparator import CBOMComparator
from app.cbom.validator import CBOMValidator
from app.migration.sandbox import SandboxEnvironment
from app.migration.transformer import MigrationTransformer
from app.validation.regression import RegressionValidationService

class CBOMDiffValidationService:
    """
    Orchestrator for Before/After CBOM Comparison Pipeline (Priority 2 Task #8).
    
    Architectural Rules:
    1. Reuses original canonical CBOM pipeline (no second CBOM generator).
    2. Loads BEFORE CBOM directly from `Scan.cbom_json`.
    3. Never modifies or overwrites the original BEFORE scan.
    4. Runs existing discovery & scanner pipeline against migrated sandbox to produce AFTER Scan & AFTER CBOM.
    5. Performs deterministic CBOM comparison via CBOMComparator.
    6. Integrates Task #7 regression build/test verification results.
    """

    def __init__(self, db: Session):
        self.db = db
        self.proj_repo = ProjectRepository(db)
        self.scan_repo = ScanRepository(db)
        self.val_repo = ValidationRepository(db)
        self.comparator = CBOMComparator()
        self.validator = CBOMValidator()
        self.orchestrator = ScanOrchestrator()
        self.regression_service = RegressionValidationService(db)

    def run_cbom_diff_pipeline(
        self,
        project_id: str,
        scan_id: Optional[str] = None,
        simulation_id: Optional[str] = None,
        migration_plan_id: Optional[str] = None,
        asset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        dt_started = datetime.now(timezone.utc)

        # 1. Validate Project
        proj = self.proj_repo.get(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' not found.")

        # 2. Retrieve BEFORE Scan
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
            raise ValueError(f"No completed scan target path found for project '{project_id}'.")

        original_target_path = target_scan.target_path
        if not os.path.exists(original_target_path):
            raise ValueError(f"Repository source path '{original_target_path}' does not exist on disk.")

        # 3. Load BEFORE CBOM directly from original scan.cbom_json
        before_cbom = target_scan.cbom_json
        if not before_cbom:
            raise ValueError(f"CBOM not available for scan '{target_scan.id}'. Please run or complete a scan first.")

        # 4. Validate BEFORE CBOM
        if not self.validator.validate(before_cbom):
            val_run = self._create_failed_validation_run(
                project_id=project_id,
                scan_id=target_scan.id,
                simulation_id=simulation_id,
                plan_id=migration_plan_id,
                status=ValidationStatus.ERROR,
                error_msg="BEFORE CBOM failed CycloneDX 1.6 validation rules.",
                dt_started=dt_started
            )
            return {
                "id": val_run.id,
                "project_id": project_id,
                "source_scan_id": target_scan.id,
                "after_scan_id": None,
                "simulation_id": simulation_id,
                "migration_plan_id": migration_plan_id,
                "check_type": "CBOM_DIFF",
                "status": "INVALID_CBOM",
                "framework": None,
                "exit_code": None,
                "duration": round((datetime.now(timezone.utc) - dt_started).total_seconds(), 2),
                "cbom_diff": self.comparator.compare(None, None),
                "regression_result": None,
                "summary": ["BEFORE CBOM failed validation."],
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        # 5. Retrieve & Validate Migration Simulation Context
        if not simulation_id:
            raise ValueError("A valid migration simulation is required before CBOM diff validation.")

        sim = self.db.query(MigrationSimulation).filter(MigrationSimulation.id == simulation_id).first()
        if not sim:
            raise ValueError("A valid migration simulation is required before CBOM diff validation.")
        if sim.project_id != project_id:
            raise ValueError(f"Simulation '{simulation_id}' does not belong to project '{project_id}'.")
        if migration_plan_id and sim.migration_plan_id != migration_plan_id:
            raise ValueError(f"Simulation '{simulation_id}' does not belong to migration plan '{migration_plan_id}'.")
        if not sim.asset_id:
            raise ValueError("A valid migration simulation is required before CBOM diff validation.")
        if not sim.sandbox_path or not os.path.exists(sim.sandbox_path):
            raise ValueError("A valid migration simulation is required before CBOM diff validation.")

        # Check if existing simulation itself has terminal failure status
        if sim.status in ["FAILED", "MANUAL_REVIEW_REQUIRED", "BLOCKED"]:
            err_reason = sim.changes_summary.get("reason") if isinstance(sim.changes_summary, dict) else "Migration simulation failed."
            val_run = self._create_failed_validation_run(
                project_id=project_id,
                scan_id=target_scan.id,
                simulation_id=simulation_id,
                plan_id=migration_plan_id,
                asset_id=sim.asset_id,
                status=ValidationStatus.MIGRATION_FAILED,
                error_msg=err_reason,
                dt_started=dt_started
            )
            return {
                "id": val_run.id,
                "project_id": project_id,
                "source_scan_id": target_scan.id,
                "after_scan_id": None,
                "simulation_id": simulation_id,
                "migration_plan_id": migration_plan_id,
                "asset_id": sim.asset_id,
                "check_type": "CBOM_DIFF",
                "status": "MIGRATION_FAILED",
                "framework": None,
                "exit_code": None,
                "duration": round((datetime.now(timezone.utc) - dt_started).total_seconds(), 2),
                "cbom_diff": None,
                "regression_result": {
                    "status": "MIGRATION_FAILED",
                    "regression_detected": False,
                    "reasons": [err_reason]
                },
                "summary": [f"Migration failed: {err_reason}"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        sandbox_dir = sim.sandbox_path

        # 6. Execute Canonical Scanner Pipeline against Migrated Sandbox to produce AFTER Scan & AFTER CBOM
        after_scan = self.scan_repo.create(
            project_id=project_id,
            target_path=sandbox_dir,
            scan_type="after_migration"
        )

        self.orchestrator.run_scan(after_scan.id, self.db)
        self.db.refresh(after_scan)

        after_cbom = after_scan.cbom_json
        if not after_cbom:
            raise RuntimeError("Scanner pipeline failed to generate AFTER CBOM for migrated sandbox.")

        # 7. Validate AFTER CBOM
        if not self.validator.validate(after_cbom):
            val_run = self._create_failed_validation_run(
                project_id=project_id,
                scan_id=target_scan.id,
                simulation_id=simulation_id,
                plan_id=migration_plan_id,
                asset_id=sim.asset_id,
                status=ValidationStatus.ERROR,
                error_msg="AFTER CBOM failed CycloneDX 1.6 validation rules.",
                dt_started=dt_started
            )
            return {
                "id": val_run.id,
                "project_id": project_id,
                "source_scan_id": target_scan.id,
                "after_scan_id": after_scan.id,
                "simulation_id": simulation_id,
                "migration_plan_id": migration_plan_id,
                "asset_id": sim.asset_id,
                "check_type": "CBOM_DIFF",
                "status": "INVALID_CBOM",
                "framework": None,
                "exit_code": None,
                "duration": round((datetime.now(timezone.utc) - dt_started).total_seconds(), 2),
                "cbom_diff": self.comparator.compare(before_cbom, None),
                "regression_result": None,
                "summary": ["AFTER CBOM failed validation."],
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        # 8. Deterministic CBOM Comparison
        cbom_diff_result = self.comparator.compare(before_cbom, after_cbom)

        # 9. Execute Task #7 Regression Validation (Build & Test checks)
        before_build = self.regression_service.execute_build_check(original_target_path, project_id, target_scan.id)
        before_test = self.regression_service.execute_test_check(original_target_path, project_id, target_scan.id)
        after_build = self.regression_service.execute_build_check(sandbox_dir, project_id, after_scan.id)
        after_test = self.regression_service.execute_test_check(sandbox_dir, project_id, after_scan.id)

        regression_analysis = self.regression_service.analyzer.analyze(before_build, before_test, after_build, after_test)

        dt_completed = datetime.now(timezone.utc)
        val_status_str = cbom_diff_result["status"]

        val_run_status = ValidationStatus.NO_REGRESSION if regression_analysis["status"] == "NO_REGRESSION" else ValidationStatus.REGRESSION

        # 10. Persist Traceable ValidationRun
        val_run = self.val_repo.create_validation_run(
            project_id=project_id,
            scan_id=target_scan.id,
            simulation_id=simulation_id,
            plan_id=migration_plan_id,
            asset_id=sim.asset_id,
            check_type="CBOM_DIFF",
            status=val_run_status,
            output_summary=cbom_diff_result["summary"][0] if cbom_diff_result["summary"] else "",
            evidence={
                "before_scan_id": target_scan.id,
                "after_scan_id": after_scan.id,
                "cbom_diff": cbom_diff_result,
                "regression_result": regression_analysis
            },
            duration=round((dt_completed - dt_started).total_seconds(), 2),
            logs="\n".join(cbom_diff_result["summary"]),
            started_at=dt_started,
            completed_at=dt_completed
        )

        fw = after_build.get("framework") if after_build else (before_build.get("framework") if before_build else None)

        return {
            "id": val_run.id,
            "project_id": project_id,
            "source_scan_id": target_scan.id,
            "after_scan_id": after_scan.id,
            "simulation_id": simulation_id,
            "migration_plan_id": migration_plan_id,
            "asset_id": sim.asset_id,
            "check_type": "CBOM_DIFF",
            "status": val_status_str,
            "framework": fw,
            "exit_code": None,
            "duration": round((dt_completed - dt_started).total_seconds(), 2),
            "cbom_diff": cbom_diff_result,
            "regression_result": regression_analysis,
            "created_at": dt_completed.isoformat()
        }


    def _create_failed_validation_run(
        self,
        project_id: str,
        scan_id: str,
        simulation_id: Optional[str],
        plan_id: Optional[str],
        status: ValidationStatus,
        error_msg: str,
        dt_started: datetime
    ) -> ValidationRun:
        dt_completed = datetime.now(timezone.utc)
        return self.val_repo.create_validation_run(
            project_id=project_id,
            scan_id=scan_id,
            simulation_id=simulation_id,
            plan_id=plan_id,
            check_type="CBOM_DIFF",
            status=status,
            output_summary=error_msg,
            logs=error_msg,
            started_at=dt_started,
            completed_at=dt_completed
        )
