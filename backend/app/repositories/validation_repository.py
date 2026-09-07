from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.db_models import ValidationRun
from app.models.enums import ValidationStatus

class ValidationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_validation_run(
        self,
        simulation_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        check_type: str = "BUILD",
        status: ValidationStatus = ValidationStatus.PENDING,
        command: Optional[str] = None,
        exit_code: Optional[int] = None,
        output_summary: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
        duration: float = 0.0,
        build_passed: bool = False,
        unit_tests_passed: bool = False,
        crypto_tests_passed: bool = False,
        integration_tests_passed: bool = False,
        regression_passed: bool = False,
        api_compatible: bool = False,
        logs: Optional[str] = None,
        residual_risk_score: float = 0.0,
        confidence: float = 1.0
    ) -> ValidationRun:
        run = ValidationRun(
            simulation_id=simulation_id,
            plan_id=plan_id,
            asset_id=asset_id,
            check_type=check_type,
            status=status,
            command=command,
            exit_code=exit_code,
            output_summary=output_summary,
            evidence=evidence,
            duration=duration,
            build_passed=build_passed,
            unit_tests_passed=unit_tests_passed,
            crypto_tests_passed=crypto_tests_passed,
            integration_tests_passed=integration_tests_passed,
            regression_passed=regression_passed,
            api_compatible=api_compatible,
            logs=logs,
            residual_risk_score=residual_risk_score,
            confidence=confidence
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get(self, validation_id: str) -> Optional[ValidationRun]:
        return self.db.query(ValidationRun).filter(ValidationRun.id == validation_id).first()

    def get_by_simulation(self, simulation_id: str) -> List[ValidationRun]:
        return self.db.query(ValidationRun).filter(ValidationRun.simulation_id == simulation_id).order_by(desc(ValidationRun.created_at)).all()

    def list_all(self) -> List[ValidationRun]:
        return self.db.query(ValidationRun).order_by(desc(ValidationRun.created_at)).all()
