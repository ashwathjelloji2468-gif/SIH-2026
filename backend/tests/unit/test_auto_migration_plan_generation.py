import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.db_models import Base, Project, Scan, CryptoAsset, Recommendation, MigrationPlan, MigrationTask
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety, RecommendationCategory
from app.orchestration.scan_orchestrator import ScanOrchestrator
from app.repositories.migration_repository import MigrationRepository

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_auto_migration_plan_generation_on_scan(db_session):
    with tempfile.TemporaryDirectory() as temp_dir:
        target_file = os.path.join(temp_dir, "auth_crypto.py")
        with open(target_file, "w") as f:
            f.write(
                "from cryptography.hazmat.primitives.asymmetric import rsa\n"
                "key = rsa.generate_private_key(65537, 2048)\n"
            )

        proj = Project(name="real-production-repo", repository_url=temp_dir)
        db_session.add(proj)
        db_session.commit()

        scan = Scan(project_id=proj.id, target_path=temp_dir, status=ScanStatus.QUEUED)
        db_session.add(scan)
        db_session.commit()

        orchestrator = ScanOrchestrator()
        orchestrator.run_scan(scan.id, db_session)
        orchestrator.run_post_scan_enrichment(scan.id, db_session)

        # TEST 1 & TEST 2: Successful scan creates and persists MigrationPlan
        repo = MigrationRepository(db_session)
        plans = repo.get_plans_by_project(proj.id)
        assert len(plans) == 1, "MigrationPlan should be automatically generated and persisted"

        plan = plans[0]

        # TEST 3: The created plan references actual project_id
        assert plan.project_id == proj.id

        # TEST 4 & TEST 5: The created plan tasks reference actual assets & recommendations
        tasks = repo.get_tasks_for_plan(plan.id)
        assert len(tasks) > 0, "Tasks should be generated for discovered crypto assets"
        
        for task in tasks:
            assert task.project_id == proj.id
            assert task.asset_id is not None
            # Ensure asset exists in DB
            asset = db_session.query(CryptoAsset).filter(CryptoAsset.id == task.asset_id).first()
            assert asset is not None
            assert asset.scan_id == scan.id

        # TEST 6: Running the same scan orchestration twice does not create duplicate plans (Idempotency)
        orchestrator.run_scan(scan.id, db_session)
        plans_after_rerun = repo.get_plans_by_project(proj.id)
        assert len(plans_after_rerun) == 1, "Idempotency check: duplicate plans should not be created"

        # TEST 7: Sim Project/test-fixture records are not used as fallback
        assert proj.name == "real-production-repo"
        assert "Sim Project" not in plan.name
