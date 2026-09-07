from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.db_models import MigrationSimulation
from app.models.enums import SimulationStatus

class MigrationSimulationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_simulation(
        self,
        asset_id: str,
        project_id: Optional[str] = None,
        recommendation_id: Optional[str] = None,
        migration_plan_id: Optional[str] = None,
        sandbox_path: Optional[str] = None,
        transformation_type: Optional[str] = None,
        status: SimulationStatus = SimulationStatus.CREATED
    ) -> MigrationSimulation:
        sim = MigrationSimulation(
            asset_id=asset_id,
            project_id=project_id,
            recommendation_id=recommendation_id,
            migration_plan_id=migration_plan_id,
            sandbox_path=sandbox_path,
            transformation_type=transformation_type,
            status=status
        )
        self.db.add(sim)
        self.db.commit()
        self.db.refresh(sim)
        return sim

    def get(self, simulation_id: str) -> Optional[MigrationSimulation]:
        return self.db.query(MigrationSimulation).filter(MigrationSimulation.id == simulation_id).first()

    def get_by_asset(self, asset_id: str) -> List[MigrationSimulation]:
        return self.db.query(MigrationSimulation).filter(MigrationSimulation.asset_id == asset_id).order_by(desc(MigrationSimulation.created_at)).all()

    def list_simulations(self, project_id: Optional[str] = None) -> List[MigrationSimulation]:
        query = self.db.query(MigrationSimulation)
        if project_id:
            query = query.filter(MigrationSimulation.project_id == project_id)
        return query.order_by(desc(MigrationSimulation.created_at)).all()

    def update_simulation_result(
        self,
        simulation_id: str,
        status: SimulationStatus,
        files_changed: Optional[List[str]] = None,
        changes_summary: Optional[Dict[str, Any]] = None,
        before_fingerprint: Optional[str] = None,
        after_fingerprint: Optional[str] = None,
        validation_result: Optional[Dict[str, Any]] = None,
        failure_reason: Optional[str] = None,
        blocker_reason: Optional[str] = None
    ) -> Optional[MigrationSimulation]:
        sim = self.get(simulation_id)
        if not sim:
            return None

        sim.status = status
        if files_changed is not None:
            sim.files_changed = files_changed
        if changes_summary is not None:
            sim.changes_summary = changes_summary
        if before_fingerprint is not None:
            sim.before_fingerprint = before_fingerprint
        if after_fingerprint is not None:
            sim.after_fingerprint = after_fingerprint
        if validation_result is not None:
            sim.validation_result = validation_result
        if failure_reason is not None:
            sim.failure_reason = failure_reason
        if blocker_reason is not None:
            sim.blocker_reason = blocker_reason

        self.db.commit()
        self.db.refresh(sim)
        return sim
