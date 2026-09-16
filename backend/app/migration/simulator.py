import os
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.repositories.asset_repository import AssetRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.migration_simulation_repository import MigrationSimulationRepository
from app.repositories.validation_repository import ValidationRepository
from app.migration.sandbox import SandboxEnvironment, SandboxConfig
from app.migration.transformer import MigrationTransformer
from app.migration.comparison import BeforeAfterComparer
from app.validation.validator import MigrationValidator
from app.models.enums import SimulationStatus, ValidationStatus
from app.scanners.source_scanner import SourceScanner
from app.scanners.dependency_scanner import DependencyScanner
from app.scanners.certificate_scanner import CertificateScanner
from app.cbom.cyclonedx_adapter import generate_cbom_json
from app.cbom.comparator import CBOMComparator
from app.engines.x_engine import XEngine
from app.engines.y_engine import YEngine
from app.engines.z_engine import ZEngine
from app.engines.mosca_engine import MoscaEngine

class MigrationSimulator:
    """
    Migration Simulator & Validation Orchestrator for SENTRIQ.
    Orchestrates isolated baseline vs working sandbox workspace directories,
    conservative deterministic code transformations, before/after diff analysis,
    migrated CBOM scanning & diffing, canonical risk re-evaluation,
    automated validation gates, and database persistence.
    """
    def run_simulation(
        self,
        db: Session,
        asset_id: str,
        source_directory_override: Optional[str] = None,
        migration_plan_id: Optional[str] = None,
        requested_pattern: Optional[str] = None
    ) -> Dict[str, Any]:

        asset_repo = AssetRepository(db)
        rec_repo = RecommendationRepository(db)
        sim_repo = MigrationSimulationRepository(db)
        val_repo = ValidationRepository(db)

        asset = asset_repo.get(asset_id)
        if not asset:
            raise ValueError(f"Crypto asset '{asset_id}' not found.")

        recommendation = rec_repo.get_latest_for_asset(asset_id)
        scan = getattr(asset, "scan", None)
        project_id = getattr(scan, "project_id", None) or getattr(asset, "project_id", None)

        # 1. Create Simulation record in DB
        simulation = sim_repo.create_simulation(
            asset_id=asset_id,
            project_id=project_id,
            recommendation_id=getattr(recommendation, "id", None),
            migration_plan_id=migration_plan_id,
            status=SimulationStatus.PREPARING
        )

        config = SandboxConfig()
        sandbox = SandboxEnvironment(simulation_id=simulation.id, config=config)

        try:
            # 2. Source Resolution (Requirement 5)
            source_path = source_directory_override
            if not source_path:
                if scan and getattr(scan, "target_path", None) and os.path.exists(scan.target_path):
                    source_path = scan.target_path
                elif getattr(asset, "location", None):
                    # Check if location is a valid directory or relative file in workspace
                    loc = asset.location
                    if os.path.exists(loc):
                        source_path = os.path.dirname(loc) if os.path.isfile(loc) else loc
                    elif os.path.exists(os.path.basename(loc)):
                        source_path = os.getcwd()

            if not source_path or not os.path.exists(source_path):
                # Cannot safely resolve source repository -> BLOCKED
                sim_result = sim_repo.update_simulation_result(
                    simulation_id=simulation.id,
                    status=SimulationStatus.BLOCKED,
                    blocker_reason=f"Migration source repository path '{source_path}' does not exist on disk or is unavailable."
                )
                return self._format_simulation_response(
                    sim_result, asset, recommendation, {},
                    {"overall_result": "BLOCKED", "blockers": ["Migration source repository path is unavailable."]}
                )

            # 3. Prepare Dual Sandbox Workspace (Requirement 1 & 2)
            try:
                working_dir = sandbox.prepare_sandbox(source_path=source_path)
                baseline_dir = sandbox.baseline_dir
            except ValueError as ve:
                sim_result = sim_repo.update_simulation_result(
                    simulation_id=simulation.id,
                    status=SimulationStatus.BLOCKED,
                    blocker_reason=str(ve)
                )
                return self._format_simulation_response(
                    sim_result, asset, recommendation, {},
                    {"overall_result": "BLOCKED", "blockers": [str(ve)]}
                )

            sim_repo.update_simulation_result(
                simulation_id=simulation.id,
                status=SimulationStatus.SIMULATING
            )

            # Compute Before Fingerprint from immutable baseline_dir
            comparer = BeforeAfterComparer()
            before_hash = comparer.compute_directory_fingerprint(baseline_dir)

            # Check if source language is unsupported
            if sandbox.detected_language == "unknown":
                sim_result = sim_repo.update_simulation_result(
                    simulation_id=simulation.id,
                    status=SimulationStatus.MANUAL_REVIEW_REQUIRED,
                    blocker_reason="Unsupported programming language or source structure for automated transformation."
                )
                return self._format_simulation_response(
                    sim_result, asset, recommendation, {},
                    {"overall_result": "MANUAL_REVIEW_REQUIRED", "blockers": ["Unsupported source language."]}
                )

            # 4. Apply Deterministic Transformation to working_dir ONLY (Requirement 3 & 4)
            transformer = MigrationTransformer()
            t_result = transformer.transform_sandbox_code(
                sandbox_dir=working_dir,
                asset=asset,
                recommendation=recommendation,
                requested_pattern=requested_pattern
            )
            t_status_str = t_result.get("status", "FAILED")

            # Map transformation status to SimulationStatus
            if t_status_str == "BLOCKED":
                sim_status = SimulationStatus.BLOCKED
            elif t_status_str == "MANUAL_REVIEW_REQUIRED":
                sim_status = SimulationStatus.MANUAL_REVIEW_REQUIRED
            elif t_status_str in ["TRANSFORMED", "NO_PQC_TRANSFORMATION_REQUIRED"]:
                sim_status = SimulationStatus.TRANSFORMED
            else:
                sim_status = SimulationStatus.FAILED

            # 5. Compute After Fingerprint and Comparison (baseline_dir vs working_dir) (Requirement 1 & 7)
            after_hash = comparer.compute_directory_fingerprint(working_dir)
            files_changed = t_result.get("files_changed", [])

            comparison_summary = comparer.compare(
                before_dir=baseline_dir,
                after_dir=working_dir,
                files_changed=files_changed,
                original_algorithm=getattr(asset, "algorithm_name", "UNKNOWN"),
                target_candidate=getattr(recommendation, "target_pqc_candidate", t_result.get("target_pqc_candidate", "PQC_CANDIDATE"))
            )

            # Rule 7 Check: If status == TRANSFORMED, before_fingerprint != after_fingerprint
            if t_status_str == "TRANSFORMED" and before_hash == after_hash:
                sim_status = SimulationStatus.FAILED
                t_result["unsupported_assumptions"] = ["Transformation produced no net file diff between baseline and working directories."]

            # 6. Re-scan Migrated Source & Compute CBOM Diff (Requirement 8)
            before_cbom = None
            after_cbom = None
            cbom_diff = None

            try:
                scanners = [SourceScanner(), DependencyScanner(), CertificateScanner()]
                # Scan baseline_dir
                base_raw = []
                for sc in scanners:
                    base_raw.extend(sc.scan(baseline_dir))
                dummy_scan = scan or type("DummyScan", (), {"id": simulation.id})()
                before_cbom = generate_cbom_json(dummy_scan, base_raw)

                # Scan working_dir
                work_raw = []
                for sc in scanners:
                    work_raw.extend(sc.scan(working_dir))
                after_cbom = generate_cbom_json(dummy_scan, work_raw)

                cbom_diff = CBOMComparator().compare(before_cbom, after_cbom)
                comparison_summary["cbom_diff"] = cbom_diff
            except Exception as e:
                cbom_diff = {"status": "ERROR", "summary": [f"CBOM re-scan error: {str(e)}"]}

            # 7. Execute Automated Validation (Requirement 9, 10, 11)
            validator = MigrationValidator()
            val_summary = validator.validate_simulation(
                sandbox_dir=working_dir,
                transformation_result=t_result,
                asset=asset,
                recommendation=recommendation
            )

            # 8. Canonical Risk Re-Evaluation (Requirement 13)
            post_migration_risk = None
            try:
                project_x = getattr(asset.scan.project, "user_x_years", 10) if (asset.scan and asset.scan.project) else 10
                project_y_scenario = getattr(asset.scan.project, "user_y_scenario", "STANDARD") if (asset.scan and asset.scan.project) else "STANDARD"
                y_res = YEngine().evaluate_migration_time(scenario=project_y_scenario)
                project_y = y_res.get("value", 10.0)

                z_res = ZEngine().evaluate_artifact_z(asset)
                z_i = z_res.get("z_value")

                if z_i is not None:
                    mosca_res = MoscaEngine().evaluate_urgency(x_years=project_x, y_years=project_y, z_years=z_i)
                    m_i = mosca_res.get("mosca_score")
                    post_migration_risk = {
                        "x": project_x,
                        "y": project_y,
                        "z_i": z_i,
                        "m_i": m_i,
                        "mosca_status": mosca_res.get("mosca_status")
                    }
            except Exception:
                pass

            if post_migration_risk:
                val_summary["post_migration_risk"] = post_migration_risk

            # 9. Determine Final Simulation Status (Requirement 12)
            if sim_status == SimulationStatus.BLOCKED:
                final_sim_status = SimulationStatus.BLOCKED
            elif sim_status == SimulationStatus.MANUAL_REVIEW_REQUIRED:
                final_sim_status = SimulationStatus.MANUAL_REVIEW_REQUIRED
            elif (
                (t_status_str == "NO_PQC_TRANSFORMATION_REQUIRED" or (t_status_str == "TRANSFORMED" and before_hash != after_hash)) and
                val_summary.get("crypto_tests_passed", False) is True and
                val_summary.get("overall_result") not in ["FAILED", "TIMEOUT", "ERROR"]
            ):
                final_sim_status = SimulationStatus.PASSED
            else:
                final_sim_status = SimulationStatus.FAILED

            # 10. Persist Validation Runs
            if simulation.migration_plan_id:
                for check in val_summary.get("check_runs", []):
                    val_repo.create_validation_run(
                        simulation_id=simulation.id,
                        plan_id=simulation.migration_plan_id,
                        asset_id=asset_id,
                        check_type=check.get("check_type", "BUILD"),
                        status=ValidationStatus.PASSED if check.get("status") == "PASS" else ValidationStatus.FAILED,
                        command=check.get("command"),
                        exit_code=check.get("exit_code"),
                        output_summary=check.get("output_summary"),
                        evidence=check.get("evidence"),
                        duration=check.get("duration", 0.0),
                        build_passed=val_summary.get("build_passed", False),
                        unit_tests_passed=val_summary.get("unit_tests_passed", False),
                        crypto_tests_passed=val_summary.get("crypto_tests_passed", False),
                        integration_tests_passed=val_summary.get("integration_tests_passed", False),
                        regression_passed=val_summary.get("regression_passed", False),
                        api_compatible=val_summary.get("api_compatible", False),
                        logs=val_summary.get("logs")
                    )

            # Update final simulation record (Requirement 14)
            updated_sim = sim_repo.update_simulation_result(
                simulation_id=simulation.id,
                status=final_sim_status,
                files_changed=files_changed,
                changes_summary=comparison_summary,
                before_fingerprint=before_hash,
                after_fingerprint=after_hash,
                validation_result=val_summary,
                failure_reason=t_result.get("changes_summary", {}).get("error") if final_sim_status == SimulationStatus.FAILED else None,
                blocker_reason=t_result.get("unsupported_assumptions", [None])[0] if final_sim_status in [SimulationStatus.BLOCKED, SimulationStatus.MANUAL_REVIEW_REQUIRED] else None
            )

            return self._format_simulation_response(updated_sim, asset, recommendation, comparison_summary, val_summary)

        finally:
            sandbox.cleanup()

    def _format_simulation_response(
        self,
        sim: Any,
        asset: Any,
        recommendation: Optional[Any],
        comparison: Dict[str, Any],
        validation: Dict[str, Any]
    ) -> Dict[str, Any]:

        status_val = sim.status.value if hasattr(sim.status, "value") else str(sim.status)

        return {
            "simulation_id": sim.id,
            "asset_id": sim.asset_id,
            "project_id": sim.project_id,
            "recommendation": {
                "current_algorithm": getattr(asset, "algorithm_name", "UNKNOWN"),
                "target_algorithm": getattr(recommendation, "target_pqc_candidate", "ML-KEM") if recommendation else "ML-KEM",
                "recommended_algorithm": getattr(recommendation, "recommended_algorithm", "ML-KEM") if recommendation else "ML-KEM",
                "category": getattr(recommendation, "category", "MANUAL_REVIEW").value if hasattr(getattr(recommendation, "category", "MANUAL_REVIEW"), "value") else str(getattr(recommendation, "category", "MANUAL_REVIEW"))
            } if recommendation else {
                "current_algorithm": getattr(asset, "algorithm_name", "UNKNOWN"),
                "target_algorithm": "ML-KEM",
                "recommended_algorithm": "ML-KEM",
                "category": "MANUAL_REVIEW"
            },
            "status": status_val,
            "sandbox_path": sim.sandbox_path,
            "transformation_type": sim.transformation_type,
            "files_changed": sim.files_changed or [],
            "before": {
                "fingerprint": sim.before_fingerprint,
                "algorithm": getattr(asset, "algorithm_name", "UNKNOWN")
            },
            "after": {
                "fingerprint": sim.after_fingerprint,
                "algorithms": comparison.get("algorithms_after", [getattr(asset, "algorithm_name", "UNKNOWN")])
            },
            "changes_summary": sim.changes_summary or comparison,
            "validation": {
                "overall_result": validation.get("overall_result", "NOT_VALIDATED"),
                "syntax_passed": validation.get("build_passed", False),
                "build_passed": validation.get("build_passed", False),
                "unit_tests_passed": validation.get("unit_tests_passed", False),
                "crypto_tests_passed": validation.get("crypto_tests_passed", False),
                "integration_tests_passed": validation.get("integration_tests_passed", False),
                "regression_passed": validation.get("regression_passed", False),
                "check_runs_count": len(validation.get("check_runs", []))
            },
            "blockers": validation.get("blockers", []),
            "failure_reason": sim.failure_reason,
            "blocker_reason": sim.blocker_reason,
            "logs": validation.get("logs", ""),
            "confidence": getattr(sim, "confidence", 1.0),
            "created_at": sim.created_at.isoformat() if hasattr(sim.created_at, "isoformat") else str(sim.created_at)
        }

