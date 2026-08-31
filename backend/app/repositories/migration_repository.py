from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.db_models import MigrationPlan, MigrationTask, ValidationRun
from app.models.enums import ValidationStatus

class MigrationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_plan(self, project_id: str, name: str, total_person_days: float = 0.0, total_calendar_months: float = 0.0, assumptions: Optional[dict] = None) -> MigrationPlan:
        db_obj = MigrationPlan(
            project_id=project_id,
            name=name,
            total_person_days=total_person_days,
            total_calendar_months=total_calendar_months,
            assumptions=assumptions or {}
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_plan(self, plan_id: str) -> Optional[MigrationPlan]:
        return self.db.query(MigrationPlan).filter(MigrationPlan.id == plan_id).first()

    def get_plans_by_project(self, project_id: str) -> List[MigrationPlan]:
        return self.db.query(MigrationPlan).filter(MigrationPlan.project_id == project_id).all()

    def add_task(self, plan_id: str, asset_id: str, title: str, person_days: float = 1.0, sequence_order: int = 1, description: Optional[str] = None) -> MigrationTask:
        task = MigrationTask(
            plan_id=plan_id,
            asset_id=asset_id,
            title=title,
            description=description,
            person_days=person_days,
            sequence_order=sequence_order
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def create_validation_run(self, plan_id: str, status: ValidationStatus = ValidationStatus.PENDING, build_passed: bool = False, unit_tests_passed: bool = False, crypto_tests_passed: bool = False, logs: Optional[str] = None) -> ValidationRun:
        run = ValidationRun(
            plan_id=plan_id,
            status=status,
            build_passed=build_passed,
            unit_tests_passed=unit_tests_passed,
            crypto_tests_passed=crypto_tests_passed,
            logs=logs
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_validation_run(self, validation_id: str) -> Optional[ValidationRun]:
        return self.db.query(ValidationRun).filter(ValidationRun.id == validation_id).first()
