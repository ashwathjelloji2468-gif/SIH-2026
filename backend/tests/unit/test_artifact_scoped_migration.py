import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.db_models import (
    Project, Scan, CryptoAsset, MigrationPlan, MigrationTask, MigrationSimulation, ValidationRun
)
from app.models.enums import AssetType, CryptoPurpose
from app.migration.planner import MigrationPlanner


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_artifact_scoped_migration_flow_and_cross_artifact(client, db_session):
    with tempfile.TemporaryDirectory() as tmpdir:
        proj = Project(id="proj-scoped-1", name="Scoped Test Project")
        scan = Scan(id="scan-scoped-1", project_id=proj.id, target_path=tmpdir)
        db_session.add_all([proj, scan])
        db_session.commit()

        asset_a = CryptoAsset(
            id="asset-rsa-a",
            scan_id=scan.id,
            name="RSA-2048 Key",
            algorithm_name="RSA-2048",
            location="src/rsa.py",
            asset_type=AssetType.ALGORITHM,
            purpose=CryptoPurpose.SIGNATURE
        )
        asset_b = CryptoAsset(
            id="asset-ecdh-b",
            scan_id=scan.id,
            name="ECDH-P256 Key",
            algorithm_name="ECDH-P256",
            location="src/ecdh.py",
            asset_type=AssetType.ALGORITHM,
            purpose=CryptoPurpose.KEY_ESTABLISHMENT
        )
        db_session.add_all([asset_a, asset_b])
        db_session.commit()

        planner = MigrationPlanner()
        plan = planner.create_plan_for_project(
            db_session, project_id=proj.id, plan_name="Multi-Asset Test Plan", assets=[asset_a, asset_b]
        )
        db_session.commit()

        # TEST 1 & TEST 2 & TEST 3 & CROSS-ARTIFACT:
        # Simulate Asset A via API (assert simulation.asset_id == Asset A.id)
        res_a = client.post(f"/api/v1/migration/plans/{plan.id}/simulate?asset_id={asset_a.id}")
        assert res_a.status_code == 200, res_a.text
        sim_a_id = res_a.json()["simulation_id"]
        sim_a = db_session.query(MigrationSimulation).get(sim_a_id)
        assert sim_a.asset_id == asset_a.id

        # Simulate Asset B via API (assert simulation.asset_id == Asset B.id and NOT plan.tasks[0].asset_id)
        res_b = client.post(f"/api/v1/migration/plans/{plan.id}/simulate?asset_id={asset_b.id}")
        assert res_b.status_code == 200, res_b.text
        sim_b_id = res_b.json()["simulation_id"]
        sim_b = db_session.query(MigrationSimulation).get(sim_b_id)
        assert sim_b.asset_id == asset_b.id

        # Assert Cross-Artifact Verification
        assert sim_a.asset_id != sim_b.asset_id
        assert sim_a.id != sim_b.id

        # TEST 4: Asset ID not belonging to the migration plan is rejected
        res_invalid = client.post(f"/api/v1/migration/plans/{plan.id}/simulate?asset_id=nonexistent-asset-999")
        assert res_invalid.status_code in (400, 404)

        # TEST 5: Stage 3 validates the simulation ID returned by Stage 2
        val_res_a = client.post(f"/api/v1/migration/simulations/{sim_a_id}/validate")
        assert val_res_a.status_code == 200, val_res_a.text
        val_a = db_session.query(ValidationRun).filter_by(simulation_id=sim_a_id).first()
        assert val_a is not None
        assert val_a.simulation_id == sim_a_id

        # TEST 7: Existing no-asset_id behavior remains unchanged
        res_default = client.post(f"/api/v1/migration/plans/{plan.id}/simulate")
        assert res_default.status_code == 200, res_default.text
        sim_def_id = res_default.json()["simulation_id"]
        sim_def = db_session.query(MigrationSimulation).get(sim_def_id)
        assert sim_def.asset_id == plan.tasks[0].asset_id
