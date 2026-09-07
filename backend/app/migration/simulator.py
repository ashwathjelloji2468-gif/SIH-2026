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

class MigrationSimulator:
    """
    Migration Simulator & Validation Orchestrator for SENTRIQ (Prompt 6).
    Orchestrates isolated sandbox workspace, conservative code transformations,
    before/after analysis, automated validation checks, and database persistence.
    """
    def run_simulation(
        self,
        db: Session,
        asset_id: str,
        source_directory_override: Optional[str] = None
    ) -> Dict[str, Any]:

        asset_repo = AssetRepository(db)
        rec_repo = RecommendationRepository(db)
        sim_repo = MigrationSimulationRepository(db)
        val_repo = ValidationRepository(db)

        asset = asset_repo.get(asset_id)
        if not asset:
            raise ValueError(f"Crypto asset '{asset_id}' not found.")

        recommendation = rec_repo.get_latest_for_asset(asset_id)
        project_id = getattr(getattr(asset, "scan", None), "project_id", None)

        # 1. Create Simulation record in DB
        simulation = sim_repo.create_simulation(
            asset_id=asset_id,
            project_id=project_id,
            recommendation_id=getattr(recommendation, "id", None),
            status=SimulationStatus.PREPARING
        )

        config = SandboxConfig()
        sandbox = SandboxEnvironment(simulation_id=simulation.id, config=config)

        try:
            # 2. Prepare Sandbox Workspace
            source_path = source_directory_override or getattr(asset, "location", None)
            if source_path and not os.path.isabs(source_path):
                # Attempt to locate source_path relative to current directory if not absolute
                if os.path.exists(source_path):
                    source_path = os.path.abspath(source_path)

            sandbox_dir = sandbox.prepare_sandbox(source_path=source_path)
            sim_repo.update_simulation_result(
                simulation_id=simulation.id,
                status=SimulationStatus.SIMULATING
            )

            # Compute Before Fingerprint
            comparer = BeforeAfterComparer()
            before_hash = comparer.compute_directory_fingerprint(sandbox_dir)

            # Check if source language is unsupported
            if sandbox.detected_language == "unknown":
                sim_result = sim_repo.update_simulation_result(
                    simulation_id=simulation.id,
                    status=SimulationStatus.MANUAL_REVIEW_REQUIRED,
                    blocker_reason="Unsupported programming language or source structure for automated transformation."
                )
                return self._format_simulation_response(sim_result, asset, recommendation, {}, {"overall_result": "MANUAL_REVIEW_REQUIRED"})

            # 3. Apply Deterministic Transformation
            transformer = MigrationTransformer()
            t_result = transformer.transform_sandbox_code(sandbox_dir, asset, recommendation)
            t_status_str = t_result.get("status", "FAILED")

            # Map transformation status to SimulationStatus enum
            if t_status_str == "MANUAL_REVIEW_REQUIRED":
                sim_status = SimulationStatus.MANUAL_REVIEW_REQUIRED
            elif t_status_str in ["TRANSFORMED", "NO_PQC_TRANSFORMATION_REQUIRED"]:
                sim_status = SimulationStatus.TRANSFORMED
            else:
                sim_status = SimulationStatus.FAILED

            # Compute After Fingerprint and Comparison
            after_hash = comparer.compute_directory_fingerprint(sandbox_dir)
            files_changed = t_result.get("files_changed", [])
            comparison_summary = comparer.compare(
                before_dir=sandbox_dir,
                after_dir=sandbox_dir,
                files_changed=files_changed,
                original_algorithm=getattr(asset, "algorithm_name", "UNKNOWN"),
                target_candidate=getattr(recommendation, "target_pqc_candidate", "PQC_CANDIDATE")
            )

            # 4. Execute Automated Validation
            validator = MigrationValidator()
            val_summary = validator.validate_simulation(
                sandbox_dir=sandbox_dir,
                transformation_result=t_result,
                asset=asset,
                recommendation=recommendation
            )

            # Determine Final Simulation Status
            if sim_status == SimulationStatus.MANUAL_REVIEW_REQUIRED:
                final_sim_status = SimulationStatus.MANUAL_REVIEW_REQUIRED
            elif val_summary.get("overall_result") == "PASSED":
                final_sim_status = SimulationStatus.PASSED
            else:
                final_sim_status = SimulationStatus.FAILED

            # 5. Persist Validation Runs only if simulation is associated with a MigrationPlan
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


            # Update final simulation state
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
