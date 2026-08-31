from typing import List
from app.repositories.migration_repository import MigrationRepository
from app.migration.effort_estimator import estimate_migration_effort
from app.models.db_models import CryptoAsset, MigrationPlan

class MigrationPlanner:
    def create_plan_for_project(self, db, project_id: str, plan_name: str, assets: List[CryptoAsset]) -> MigrationPlan:
        repo = MigrationRepository(db)
        
        effort = estimate_migration_effort(
            affected_assets_count=len(assets),
            dependency_count=len(assets) // 2
        )

        plan = repo.create_plan(
            project_id=project_id,
            name=plan_name,
            total_person_days=effort["person_days"],
            total_calendar_months=effort["calendar_months"],
            assumptions=effort["assumptions"]
        )

        for idx, asset in enumerate(assets, start=1):
            repo.add_task(
                plan_id=plan.id,
                asset_id=asset.id,
                title=f"Migrate {asset.algorithm_name} in {asset.location}",
                description=f"Upgrade {asset.algorithm_name} to NIST PQC candidate for purpose {asset.purpose.value}",
                person_days=5.0,
                sequence_order=idx
            )

        return plan
