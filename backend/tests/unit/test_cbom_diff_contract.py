import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.db_models import Project, Scan, MigrationPlan, ValidationRun, MigrationSimulation
from app.models.enums import ScanStatus, SimulationStatus

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)

@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_cbom_diff_missing_plan_id_returns_400(client, db_session):
    p = Project(id="proj_no_plan", name="No Plan Proj")
    s = Scan(id="scan_no_plan", project_id="proj_no_plan", target_path="/tmp")
    db_session.add_all([p, s])
    db_session.commit()

    response = client.post("/api/v1/projects/proj_no_plan/validation/cbom-diff?scan_id=scan_no_plan")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "migration_plan_id is required for CBOM diff validation.",
        "error_code": "MISSING_MIGRATION_PLAN_ID"
    }

    runs = db_session.query(ValidationRun).filter(ValidationRun.project_id == "proj_no_plan").all()
    assert len(runs) == 0

def test_cbom_diff_missing_simulation_id_returns_400(client, db_session):
    p = Project(id="proj_no_sim", name="No Sim Proj")
    s = Scan(id="scan_no_sim", project_id="proj_no_sim", target_path="/tmp")
    plan = MigrationPlan(id="plan_no_sim", project_id="proj_no_sim", name="PQC Plan")
    db_session.add_all([p, s, plan])
    db_session.commit()

    response = client.post(
        "/api/v1/projects/proj_no_sim/validation/cbom-diff"
        "?scan_id=scan_no_sim&migration_plan_id=plan_no_sim"
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "A valid migration simulation is required before CBOM diff validation.",
        "error_code": "MISSING_MIGRATION_SIMULATION"
    }

def test_cbom_diff_nonexistent_simulation_returns_400(client, db_session):
    with tempfile.TemporaryDirectory() as orig_dir:
        with open(os.path.join(orig_dir, "main.py"), "w") as f:
            f.write("# orig code\n")
        p = Project(id="proj_bad_sim", name="Bad Sim Proj")
        s = Scan(
            id="scan_bad_sim",
            project_id="proj_bad_sim",
            status=ScanStatus.COMPLETED,
            target_path=orig_dir,
            cbom_json={"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []}
        )
        plan = MigrationPlan(id="plan_bad_sim", project_id="proj_bad_sim", name="PQC Plan")
        db_session.add_all([p, s, plan])
        db_session.commit()

        response = client.post(
            "/api/v1/projects/proj_bad_sim/validation/cbom-diff"
            "?scan_id=scan_bad_sim&migration_plan_id=plan_bad_sim&simulation_id=nonexistent_sim"
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": "A valid migration simulation is required before CBOM diff validation.",
            "error_code": "MISSING_MIGRATION_SIMULATION"
        }

def test_cbom_diff_deleted_sandbox_path_returns_400(client, db_session):
    with tempfile.TemporaryDirectory() as orig_dir:
        with open(os.path.join(orig_dir, "main.py"), "w") as f:
            f.write("# orig code\n")
        p = Project(id="proj_del_sb", name="Deleted Sandbox Proj")
        s = Scan(
            id="scan_del_sb",
            project_id="proj_del_sb",
            status=ScanStatus.COMPLETED,
            target_path=orig_dir,
            cbom_json={"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []}
        )
        plan = MigrationPlan(id="plan_del_sb", project_id="proj_del_sb", name="PQC Plan")
        sim = MigrationSimulation(
            id="sim_del_sb",
            migration_plan_id="plan_del_sb",
            project_id="proj_del_sb",
            asset_id="asset_123",
            status=SimulationStatus.TRANSFORMED,
            sandbox_path="/tmp/nonexistent_deleted_sandbox_dir_98765"
        )
        db_session.add_all([p, s, plan, sim])
        db_session.commit()

        response = client.post(
            "/api/v1/projects/proj_del_sb/validation/cbom-diff"
            "?scan_id=scan_del_sb&migration_plan_id=plan_del_sb&simulation_id=sim_del_sb"
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": "A valid migration simulation is required before CBOM diff validation.",
            "error_code": "MISSING_MIGRATION_SIMULATION"
        }

def test_cbom_diff_valid_simulation_uses_existing_sandbox(client, db_session):
    with tempfile.TemporaryDirectory() as orig_dir, tempfile.TemporaryDirectory() as sb_dir:
        with open(os.path.join(orig_dir, "main.py"), "w") as f:
            f.write("# original code\n")
        with open(os.path.join(sb_dir, "main.py"), "w") as f:
            f.write("# transformed code\n")

        p = Project(id="proj_valid_sim", name="Valid Sim Proj")
        s = Scan(
            id="scan_valid_sim",
            project_id="proj_valid_sim",
            status=ScanStatus.COMPLETED,
            target_path=orig_dir,
            cbom_json={"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []}
        )
        plan = MigrationPlan(id="plan_valid_sim", project_id="proj_valid_sim", name="PQC Plan")
        sim = MigrationSimulation(
            id="sim_valid_123",
            migration_plan_id="plan_valid_sim",
            project_id="proj_valid_sim",
            asset_id="asset_real_123",
            status=SimulationStatus.TRANSFORMED,
            sandbox_path=sb_dir
        )
        db_session.add_all([p, s, plan, sim])
        db_session.commit()

        response = client.post(
            "/api/v1/projects/proj_valid_sim/validation/cbom-diff"
            "?scan_id=scan_valid_sim&migration_plan_id=plan_valid_sim&simulation_id=sim_valid_123"
        )
        assert response.status_code == 200
        data = response.json()

        assert "framework" in data
        assert "exit_code" in data
        assert "duration" in data
        assert isinstance(data["duration"], (int, float))
        assert data["exit_code"] is None or isinstance(data["exit_code"], int)

        assert data["simulation_id"] == "sim_valid_123"
        assert data["migration_plan_id"] == "plan_valid_sim"
        assert data["asset_id"] == "asset_real_123"
        assert data["project_id"] == "proj_valid_sim"
        assert data["source_scan_id"] == "scan_valid_sim"

        val_run = db_session.query(ValidationRun).filter(ValidationRun.plan_id == "plan_valid_sim").first()
        assert val_run is not None
        assert val_run.simulation_id == "sim_valid_123"

def test_cbom_diff_never_uses_a_temp_fallback(client, db_session):
    with tempfile.TemporaryDirectory() as orig_dir, tempfile.TemporaryDirectory() as sb_dir:
        with open(os.path.join(orig_dir, "crypto.py"), "w") as f:
            f.write("# orig crypto\n")
        with open(os.path.join(sb_dir, "crypto.py"), "w") as f:
            f.write("# PQC crypto\n")

        p = Project(id="proj_no_atemp", name="No a_temp Proj")
        s = Scan(
            id="scan_no_atemp",
            project_id="proj_no_atemp",
            status=ScanStatus.COMPLETED,
            target_path=orig_dir,
            cbom_json={"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []}
        )
        plan = MigrationPlan(id="plan_no_atemp", project_id="proj_no_atemp", name="PQC Plan")
        sim = MigrationSimulation(
            id="sim_no_atemp",
            migration_plan_id="plan_no_atemp",
            project_id="proj_no_atemp",
            asset_id="asset_specific_456",
            status=SimulationStatus.TRANSFORMED,
            sandbox_path=sb_dir
        )
        db_session.add_all([p, s, plan, sim])
        db_session.commit()

        response = client.post(
            "/api/v1/projects/proj_no_atemp/validation/cbom-diff"
            "?scan_id=scan_no_atemp&migration_plan_id=plan_no_atemp&simulation_id=sim_no_atemp"
        )
        assert response.status_code == 200
        data = response.json()

        assert data["asset_id"] != "a_temp"
        assert data["asset_id"] == "asset_specific_456"
