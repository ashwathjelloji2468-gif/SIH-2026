from typing import List, Optional
from app.repositories.migration_repository import MigrationRepository
from app.migration.effort_estimator import estimate_migration_effort
from app.models.db_models import CryptoAsset, MigrationPlan
from app.models.enums import TestingRequirement

class MigrationPlanner:
    def create_plan_for_project(
        self,
        db,
        project_id: str,
        plan_name: str,
        assets: List[CryptoAsset],
        vendor_dependency_count: int = 1,
        pki_cert_dependency_count: int = 1,
        crypto_agility_score: float = 0.6,
        testing_requirement_level: TestingRequirement = TestingRequirement.HIGH,
        engineering_capacity_developers: int = 3
    ) -> MigrationPlan:
        repo = MigrationRepository(db)
        
        effort = estimate_migration_effort(
            affected_assets_count=len(assets),
            affected_apps_count=1,
            dependency_count=len(assets) // 2,
            vendor_dependency_count=vendor_dependency_count,
            pki_cert_dependency_count=pki_cert_dependency_count,
            crypto_agility_score=crypto_agility_score,
            testing_requirement_level=testing_requirement_level,
            business_criticality_score=80.0,
            engineering_capacity_developers=engineering_capacity_developers
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
                person_days=round(effort["person_days"] / max(1, len(assets)), 1),
                sequence_order=idx
            )

        return plan
