import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import get_db, Base
from app.models.db_models import Project, Scan, CryptoAsset, MigrationPlan, MigrationTask
from app.models.enums import AssetType, CryptoPurpose, QuantumSafety, ScanStatus

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

def test_1_projects_api_empty(client):
    """Criteria 7 & 8: Projects API returning [] results in empty list, zero fake projects inserted."""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    assert response.json() == []

def test_2_projects_api_success(client, db_session):
    """Criteria 6: Projects API returning real projects displays only backend DB records."""
    proj = Project(name="real-user-repo", description="Production repo", repository_url="https://github.com/org/repo.git")
    db_session.add(proj)
    db_session.commit()

    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "real-user-repo"
    assert "demo-bank" not in [p["name"] for p in data]

def test_3_scan_api_404_on_invalid_project(client):
    """Criteria 2: Scan API on non-existent project returns 404 error instead of fake scan."""
    response = client.post("/api/v1/projects/non-existent-proj/scans", json={"target_path": "/invalid"})
    assert response.status_code == 404

def test_4_scan_api_success(client, db_session):
    """Criteria 1: Scan API on valid project creates real Scan record."""
    proj = Project(name="scan-target-repo")
    db_session.add(proj)
    db_session.commit()
    db_session.refresh(proj)

    # Create temporary directory for real scan target
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "app.py")
        with open(test_file, "w") as f:
            f.write("from cryptography.hazmat.primitives.asymmetric import rsa\nkey = rsa.generate_private_key(65537, 2048)\n")

        response = client.post(f"/api/v1/projects/{proj.id}/scans", json={"target_path": tmpdir, "scan_type": "source"})
        response = client.post(f"/api/v1/projects/{proj.id}/scans", json={"target_path": tmpdir, "scan_type": "source"})
        assert response.status_code == 201
        scan_data = response.json()
        assert scan_data["project_id"] == proj.id
        assert scan_data["status"] in ["QUEUED", "IN_PROGRESS", "COMPLETED"]

def test_5_migration_simulation_without_valid_asset_returns_409(client, db_session):
    """Criteria 10: Migration simulation request without valid asset returns 409 Conflict instead of generating demo files."""
    proj = Project(name="empty-migration-proj")
    db_session.add(proj)
    db_session.commit()

    plan = MigrationPlan(project_id=proj.id, name="Test Migration Plan", total_person_days=5.0)
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    response = client.post(f"/api/v1/migration/plans/{plan.id}/simulate")
    assert response.status_code == 409
    assert "no cryptographic assets belong" in response.json()["detail"].lower() or "no valid assets" in response.json()["detail"].lower()

def test_6_migration_simulation_without_existing_source_returns_409(client, db_session):
    """Criteria 10: Migration request for asset without existing source path returns 409 Conflict."""
    proj = Project(name="missing-source-proj")
    db_session.add(proj)
    db_session.commit()

    scan = Scan(project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/nonexistent/path/for/test")
    db_session.add(scan)
    db_session.commit()

    asset = CryptoAsset(
        scan_id=scan.id,
        name="MissingSourceAsset",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.SIGNATURE,
        location="/nonexistent/path/for/test/file.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db_session.add(asset)
    db_session.commit()

    plan = MigrationPlan(project_id=proj.id, name="Plan for missing source asset")
    db_session.add(plan)
    db_session.commit()

    task = MigrationTask(plan_id=plan.id, asset_id=asset.id, title="Migrate RSA")
    db_session.add(task)
    db_session.commit()

    response = client.post(f"/api/v1/migration/plans/{plan.id}/simulate")
    assert response.status_code == 409
    detail = response.json()["detail"].lower()
    assert "cannot start" in detail or "does not exist" in detail or "no valid assets" in detail or "no cryptographic assets" in detail

def test_7_migration_simulation_with_real_asset_succeeds(client, db_session):
    """Criteria 11: Migration request with valid real asset and source path succeeds cleanly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_file = os.path.join(tmpdir, "crypto_module.py")
        with open(src_file, "w") as f:
            f.write("from cryptography.hazmat.primitives.asymmetric import rsa\nkey = rsa.generate_private_key(65537, 2048)\n")

        proj = Project(name="real-source-proj")
        db_session.add(proj)
        db_session.commit()

        scan = Scan(project_id=proj.id, status=ScanStatus.COMPLETED, target_path=src_file)
        db_session.add(scan)
        db_session.commit()

        asset = CryptoAsset(
            scan_id=scan.id,
            name="RealRSAAsset",
            asset_type=AssetType.ALGORITHM,
            algorithm_name="RSA-2048",
            purpose=CryptoPurpose.SIGNATURE,
            location=src_file,
            quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
        )
        db_session.add(asset)
        db_session.commit()

        plan = MigrationPlan(project_id=proj.id, name="Real Plan")
        db_session.add(plan)
        db_session.commit()

        task = MigrationTask(plan_id=plan.id, asset_id=asset.id, title="Migrate RSA")
        db_session.add(task)
        db_session.commit()
        db_session.refresh(plan)

        response = client.post(f"/api/v1/migration/plans/{plan.id}/simulate")
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.json()}"
        res = response.json()
        assert res["status"] == "SIMULATION_COMPLETED"
