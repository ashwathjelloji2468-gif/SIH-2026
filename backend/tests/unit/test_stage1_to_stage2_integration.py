"""
Stage 1 -> Stage 2 Integration Test for SENTRIQ.
Verifies that Stage 1 (migration plan creation) generates valid plan IDs and tasks in DB,
and Stage 2 (sandbox simulation) correctly retrieves the plan and executes simulation.
"""
import pytest
import app.models.db_models
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.db_models import Project, Scan, CryptoAsset
from app.models.enums import AssetType, CryptoPurpose, QuantumSafety

from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed test project, scan, asset
    proj = Project(id="proj-integration-01", name="Integration Test Project")
    db.add(proj)

    scan = Scan(id="scan-integration-01", project_id="proj-integration-01", target_path="/tmp/test", status="COMPLETED")
    db.add(scan)

    asset1 = CryptoAsset(
        id="asset-rsa-01",
        scan_id="scan-integration-01",
        name="JWT RSA Signer",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        key_size=2048,
        purpose=CryptoPurpose.SIGNATURE,
        location="src/crypto/jwt_signer.py",
        line_number=42,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    asset2 = CryptoAsset(
        id="asset-ecdsa-01",
        scan_id="scan-integration-01",
        name="TLS Handshake Handler",
        asset_type=AssetType.PROTOCOL,
        algorithm_name="ECDSA-P256",
        key_size=256,
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        location="src/network/tls_handshake.go",
        line_number=118,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db.add(asset1)
    db.add(asset2)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


def test_stage1_creates_plan_and_stage2_simulates():
    client = TestClient(app)

    # 1. Stage 1: Synthesize Migration Roadmap
    create_resp = client.post(
        "/api/v1/projects/proj-integration-01/migration/plans",
        json={
            "name": "Integration PQC Roadmap",
            "vendor_dependency_count": 2,
            "pki_cert_dependency_count": 3,
            "crypto_agility_score": 0.65,
            "testing_requirement_level": "MEDIUM",
            "engineering_capacity_developers": 4
        }
    )
    assert create_resp.status_code == 201 or create_resp.status_code == 200
    plan_data = create_resp.json()

    assert "id" in plan_data
    plan_id = plan_data["id"]
    assert plan_id is not None
    assert plan_data["project_id"] == "proj-integration-01"

    # Verify plan creation succeeds and returns valid ID
    assert plan_id is not None
    assert plan_data["project_id"] == "proj-integration-01"

    # 2. Verify GET plan returns the persisted plan and tasks
    get_resp = client.get(f"/api/v1/migration/plans/{plan_id}")
    assert get_resp.status_code == 200
    fetched_plan = get_resp.json()
    assert fetched_plan["id"] == plan_id
    assert len(fetched_plan["tasks"]) == len(plan_data["tasks"])

    # 3. Stage 2: Execute Sandbox Simulation using real plan_id
    sim_resp = client.post(f"/api/v1/migration/plans/{plan_id}/simulate?pattern=RSA_TO_ML_KEM_HYBRID")
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()

    assert sim_data["plan_id"] == plan_id
    assert sim_data["status"] == "SIMULATION_COMPLETED"
    assert "sandbox_path" in sim_data
    assert "transformation" in sim_data


def test_stage2_simulation_fails_gracefully_with_404_for_invalid_plan():
    client = TestClient(app)

    invalid_plan_id = "non-existent-plan-uuid-9999"
    sim_resp = client.post(f"/api/v1/migration/plans/{invalid_plan_id}/simulate?pattern=RSA_TO_ML_KEM_HYBRID")

    assert sim_resp.status_code == 404
    assert sim_resp.json()["detail"] == "Migration plan not found"
