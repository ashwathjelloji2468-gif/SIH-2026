from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.db_models import MigrationPlan, MigrationTask, ValidationRun
from app.models.enums import ValidationStatus

class MigrationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_plan(
        self,
        project_id: str,
        name: str,
        total_person_days: float = 0.0,
        total_calendar_months: float = 0.0,
        assumptions: Optional[dict] = None
    ) -> MigrationPlan:
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
        return self.db.query(MigrationPlan).filter(MigrationPlan.project_id == project_id).order_by(desc(MigrationPlan.created_at)).all()

    def get_tasks_for_asset(self, asset_id: str) -> List[MigrationTask]:
        return self.db.query(MigrationTask).filter(MigrationTask.asset_id == asset_id).order_by(MigrationTask.sequence_order).all()

    def get_tasks_for_plan(self, plan_id: str) -> List[MigrationTask]:
        return self.db.query(MigrationTask).filter(MigrationTask.plan_id == plan_id).order_by(MigrationTask.sequence_order).all()

    def add_task(
        self,
        plan_id: str,
        asset_id: str,
        title: str,
        person_days: float = 1.0,
        sequence_order: int = 1,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        recommendation_id: Optional[str] = None,
        task_type: str = "ALGORITHM_REPLACEMENT",
        priority: str = "P2",
        migration_complexity: str = "MEDIUM",
        status: str = "NOT_STARTED",
        affected_components: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        blockers: Optional[List[str]] = None,
        validation_requirements: Optional[List[str]] = None,
        rationale: Optional[str] = None
    ) -> MigrationTask:
        task = MigrationTask(
            plan_id=plan_id,
            project_id=project_id,
            asset_id=asset_id,
            recommendation_id=recommendation_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            migration_complexity=migration_complexity,
            person_days=person_days,
            sequence_order=sequence_order,
            status=status,
            affected_components=affected_components or [],
            dependencies=dependencies or [],
            blockers=blockers or [],
            validation_requirements=validation_requirements or [],
            rationale=rationale
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def create_validation_run(
        self,
        plan_id: str,
        status: ValidationStatus = ValidationStatus.PENDING,
        build_passed: bool = False,
        unit_tests_passed: bool = False,
        crypto_tests_passed: bool = False,
        logs: Optional[str] = None
    ) -> ValidationRun:
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
