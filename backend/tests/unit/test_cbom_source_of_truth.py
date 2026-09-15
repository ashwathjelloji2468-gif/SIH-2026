import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from app.main import app
from app.core.database import get_db, Base
from app.models.db_models import Project, Scan, CryptoAsset
from app.models.enums import ScanStatus, AssetType, CryptoPurpose
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

def test_get_scan_cbom_success(client, db_session):
    proj = Project(id="proj-1", name="Test Project")
    cbom_data = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "components": [{"name": "RSA-2048", "type": "cryptographic-asset"}]
    }
    scan = Scan(id="scan-1", project_id="proj-1", target_path="/tmp/test", status=ScanStatus.COMPLETED, cbom_json=cbom_data)
    db_session.add_all([proj, scan])
    db_session.commit()

    resp = client.get("/api/v1/scans/scan-1/cbom")
    assert resp.status_code == 200
    assert resp.json() == cbom_data

def test_get_scan_cbom_missing_returns_404(client, db_session):
    proj = Project(id="proj-1", name="Test Project")
    scan = Scan(id="scan-1", project_id="proj-1", target_path="/tmp/test", status=ScanStatus.COMPLETED, cbom_json=None)
    asset = CryptoAsset(
        id="asset-1",
        scan_id="scan-1",
        name="RSA key",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        key_size=2048,
        purpose=CryptoPurpose.ENCRYPTION,
        location="main.py"
    )
    db_session.add_all([proj, scan, asset])
    db_session.commit()

    # Must return 404 and NOT regenerate synthetic CBOM on the fly from assets
    resp = client.get("/api/v1/scans/scan-1/cbom")
    assert resp.status_code == 404
    assert "CBOM not available" in resp.json()["detail"]

def test_validate_scan_cbom_missing_returns_409(client, db_session):
    scan = Scan(id="scan-1", project_id="proj-1", target_path="/tmp/test", status=ScanStatus.COMPLETED, cbom_json=None)
    db_session.add(scan)
    db_session.commit()

    resp = client.post("/api/v1/scans/scan-1/cbom/validate")
    assert resp.status_code == 409
    assert "CBOM not available" in resp.json()["detail"]

def test_download_scan_cbom_missing_returns_409(client, db_session):
    scan = Scan(id="scan-1", project_id="proj-1", target_path="/tmp/test", status=ScanStatus.COMPLETED, cbom_json=None)
    db_session.add(scan)
    db_session.commit()

    resp = client.get("/api/v1/scans/scan-1/cbom/download")
    assert resp.status_code == 409
    assert "CBOM not available" in resp.json()["detail"]

def test_download_project_cbom_success(client, db_session):
    proj = Project(id="proj-1", name="Test Project")
    cbom_data = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "components": []
    }
    scan = Scan(id="scan-1", project_id="proj-1", target_path="/tmp/test", status=ScanStatus.COMPLETED, cbom_json=cbom_data)
    db_session.add_all([proj, scan])
    db_session.commit()

    resp = client.get("/api/v1/projects/proj-1/cbom/download")
    assert resp.status_code == 200
    assert resp.json() == cbom_data
    assert "attachment; filename=\"cbom-proj-1.json\"" in resp.headers["content-disposition"]

def test_download_project_cbom_missing_returns_409(client, db_session):
    proj = Project(id="proj-1", name="Test Project")
    db_session.add(proj)
    db_session.commit()

    # Project has no scans / no CBOM -> must return 409
    resp = client.get("/api/v1/projects/proj-1/cbom/download")
    assert resp.status_code == 409
    assert "CBOM not available" in resp.json()["detail"]

def test_scan_orchestrator_cbom_persistence(db_session, tmp_path):
    # Verify ScanOrchestrator creates and persists canonical cbom_json on scan completion
    test_dir = tmp_path / "src"
    test_dir.mkdir()
    py_file = test_dir / "crypto_sample.py"
    py_file.write_text("from cryptography.hazmat.primitives.asymmetric import rsa\nkey = rsa.generate_private_key(65537, 2048)\n")

    proj = Project(id="proj-orch", name="Orchestrator Project")
    scan = Scan(id="scan-orch", project_id=proj.id, target_path=str(test_dir), status=ScanStatus.QUEUED)
    db_session.add_all([proj, scan])
    db_session.commit()

    orchestrator = ScanOrchestrator()
    orchestrator.run_scan(scan.id, db_session)

    db_session.refresh(scan)
    assert scan.status == ScanStatus.COMPLETED
    assert scan.cbom_json is not None
    assert scan.cbom_json["bomFormat"] == "CycloneDX"
    assert scan.cbom_json["specVersion"] == "1.6"
    assert len(scan.cbom_json.get("components", [])) > 0
