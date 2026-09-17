import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

from app.main import app
from app.core.database import get_db, Base
from app.models.db_models import Project, Scan, CryptoAsset, MigrationPlan, MigrationSimulation
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, SimulationStatus
from app.validation.cbom_diff import CBOMDiffValidationService
from app.orchestration.scan_orchestrator import ScanOrchestrator

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

def test_before_cbom_uses_stored_scan_cbom(db_session, tmp_path):
    # 1. BEFORE uses scan.cbom_json directly
    test_dir = tmp_path / "src"
    test_dir.mkdir()
    (test_dir / "sample.py").write_text("from cryptography.hazmat.primitives.asymmetric import rsa\n")

    proj = Project(id="proj-sig", name="Integrity Project")
    stored_cbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "components": [
            {
                "name": "RSA-2048",
                "bom-ref": "cbom-asset-stored",
                "type": "cryptographic",
                "cryptoProperties": {
                    "assetType": "ALGORITHM",
                    "algorithmProperties": {"primitive": "ENCRYPTION", "parameterSetIdentifier": "2048"},
                    "nistQuantumSecurityLevel": 0
                },
                "evidence": {"occurrences": [{"location": "sample.py", "line": 1}]}
            }
        ]
    }
    before_scan = Scan(id="scan-before-1", project_id=proj.id, target_path=str(test_dir), status=ScanStatus.COMPLETED, cbom_json=stored_cbom)
    plan = MigrationPlan(id="plan-before-1", project_id=proj.id, name="Test Plan")
    sim = MigrationSimulation(
        id="sim-before-1",
        migration_plan_id=plan.id,
        project_id=proj.id,
        asset_id="asset-1",
        status=SimulationStatus.TRANSFORMED,
        sandbox_path=str(test_dir)
    )
    db_session.add_all([proj, before_scan, plan, sim])
    db_session.commit()

    service = CBOMDiffValidationService(db_session)
    res = service.run_cbom_diff_pipeline(
        project_id=proj.id,
        scan_id=before_scan.id,
        simulation_id=sim.id,
        migration_plan_id=plan.id
    )

    db_session.refresh(before_scan)
    # Original scan.cbom_json must remain untouched
    assert before_scan.cbom_json == stored_cbom
    assert res["source_scan_id"] == before_scan.id
    assert res["after_scan_id"] is not None
    assert res["after_scan_id"] != before_scan.id

def test_missing_before_cbom_returns_honest_error(db_session, tmp_path):
    # 2. Missing BEFORE CBOM raises ValueError / 409 and does not fabricate one
    test_dir = tmp_path / "src"
    test_dir.mkdir()

    proj = Project(id="proj-no-cbom", name="No CBOM Project")
    scan_no_cbom = Scan(id="scan-no-cbom", project_id=proj.id, target_path=str(test_dir), status=ScanStatus.COMPLETED, cbom_json=None)
    plan = MigrationPlan(id="plan-no-cbom", project_id=proj.id, name="Test Plan")
    sim = MigrationSimulation(
        id="sim-no-cbom",
        migration_plan_id=plan.id,
        project_id=proj.id,
        asset_id="asset-1",
        status=SimulationStatus.TRANSFORMED,
        sandbox_path=str(test_dir)
    )
    db_session.add_all([proj, scan_no_cbom, plan, sim])
    db_session.commit()

    service = CBOMDiffValidationService(db_session)
    with pytest.raises(ValueError) as exc_info:
        service.run_cbom_diff_pipeline(
            project_id=proj.id,
            scan_id=scan_no_cbom.id,
            simulation_id=sim.id,
            migration_plan_id=plan.id
        )

    assert "CBOM not available" in str(exc_info.value)

def test_after_cbom_uses_canonical_scanner_pipeline(db_session, tmp_path):
    # 3. AFTER uses canonical ScanOrchestrator & generate_cbom_json
    test_dir = tmp_path / "src"
    test_dir.mkdir()
    py_file = test_dir / "crypto_app.py"
    py_file.write_text("from cryptography.hazmat.primitives.asymmetric import rsa\nkey = rsa.generate_private_key(65537, 2048)\n")

    proj = Project(id="proj-after-pipe", name="After Pipeline Project")
    before_scan = Scan(id="scan-b", project_id=proj.id, target_path=str(test_dir), status=ScanStatus.COMPLETED)
    plan = MigrationPlan(id="plan-after-pipe", project_id=proj.id, name="Test Plan")
    sim = MigrationSimulation(
        id="sim-after-pipe",
        migration_plan_id=plan.id,
        project_id=proj.id,
        asset_id="asset-1",
        status=SimulationStatus.TRANSFORMED,
        sandbox_path=str(test_dir)
    )
    db_session.add_all([proj, before_scan, plan, sim])
    db_session.commit()

    # Run initial scan to populate canonical before_scan.cbom_json
    orchestrator = ScanOrchestrator()
    orchestrator.run_scan(before_scan.id, db_session)
    db_session.refresh(before_scan)

    assert before_scan.cbom_json is not None
    original_cbom_copy = dict(before_scan.cbom_json)

    service = CBOMDiffValidationService(db_session)
    res = service.run_cbom_diff_pipeline(
        project_id=proj.id,
        scan_id=before_scan.id,
        simulation_id=sim.id,
        migration_plan_id=plan.id
    )

    db_session.refresh(before_scan)
    # Original Scan remains untouched
    assert before_scan.cbom_json == original_cbom_copy

    # AFTER scan created as distinct database record with scan_type="after_migration"
    after_scan = db_session.query(Scan).filter(Scan.id == res["after_scan_id"]).first()
    assert after_scan is not None
    assert after_scan.scan_type == "after_migration"
    assert after_scan.cbom_json is not None
    assert after_scan.cbom_json["bomFormat"] == "CycloneDX"

def test_cbom_diff_endpoint_via_client(client, db_session, tmp_path):
    # 4. API endpoint POST /api/v1/projects/{project_id}/validation/cbom-diff
    test_dir = tmp_path / "src"
    test_dir.mkdir()
    py_file = test_dir / "api_crypto.py"
    py_file.write_text("from cryptography.hazmat.primitives.asymmetric import rsa\nkey = rsa.generate_private_key(65537, 2048)\n")

    proj = Project(id="proj-api-diff", name="API Diff Project")
    scan = Scan(id="scan-api-1", project_id=proj.id, target_path=str(test_dir), status=ScanStatus.QUEUED)
    plan = MigrationPlan(id="plan-api-1", project_id=proj.id, name="Test Plan")
    sim = MigrationSimulation(
        id="sim-api-1",
        migration_plan_id=plan.id,
        project_id=proj.id,
        asset_id="asset-1",
        status=SimulationStatus.TRANSFORMED,
        sandbox_path=str(test_dir)
    )
    db_session.add_all([proj, scan, plan, sim])
    db_session.commit()

    ScanOrchestrator().run_scan(scan.id, db_session)

    resp = client.post(
        f"/api/v1/projects/{proj.id}/validation/cbom-diff"
        f"?scan_id={scan.id}&migration_plan_id={plan.id}&simulation_id={sim.id}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == proj.id
    assert data["source_scan_id"] == scan.id
    assert data["migration_plan_id"] == plan.id
    assert data["simulation_id"] == sim.id
    assert data["check_type"] == "CBOM_DIFF"
    assert "cbom_diff" in data
    assert "regression_result" in data
