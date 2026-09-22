import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.db_models import Project, Scan, CryptoAsset
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety
from app.qars.models import QARSValidationError

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


def test_01_project_endpoint_success(client, db_session):
    proj = Project(id="proj_qars_1", name="Project QARS One")
    scan = Scan(id="scan_qars_1", project_id="proj_qars_1", status=ScanStatus.COMPLETED, target_path="/tmp")
    asset = CryptoAsset(
        id="asset_qars_1",
        scan_id="scan_qars_1",
        name="Asset RSA 2048",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        location="main.py"
    )
    db_session.add_all([proj, scan, asset])
    db_session.commit()

    response = client.get("/api/v1/projects/proj_qars_1/qars")
    assert response.status_code == 200
    data = response.json()

    assert data["project_id"] == "proj_qars_1"
    assert data["project_name"] == "Project QARS One"
    assert data["asset_count"] == 1
    assert len(data["assets"]) == 1

    summary = data["summary"]
    assert summary["qars_average"] is not None
    assert summary["qars_max"] is not None
    assert summary["qars_min"] is not None


def test_02_asset_endpoint_success(client, db_session):
    proj = Project(id="proj_qars_2", name="Project QARS Two")
    scan = Scan(id="scan_qars_2", project_id="proj_qars_2", status=ScanStatus.COMPLETED, target_path="/tmp")
    asset = CryptoAsset(
        id="asset_qars_2",
        scan_id="scan_qars_2",
        name="Asset RSA 2048",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_SAFE,
        location="config.py"
    )
    db_session.add_all([proj, scan, asset])
    db_session.commit()

    response = client.get("/api/v1/projects/proj_qars_2/qars/assets/asset_qars_2")
    assert response.status_code == 200
    res_json = response.json()

    assert res_json["status"] == "SUCCESS"
    assert "data" in res_json

    asset_data = res_json["data"]
    assert asset_data["asset_id"] == "asset_qars_2"
    assert asset_data["project_id"] == "proj_qars_2"
    assert asset_data["scan_id"] == "scan_qars_2"


def test_03_project_not_found(client):
    response = client.get("/api/v1/projects/non_existent_proj/qars")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_04_asset_not_found(client, db_session):
    proj = Project(id="proj_qars_3", name="Project QARS Three")
    db_session.add(proj)
    db_session.commit()

    response = client.get("/api/v1/projects/proj_qars_3/qars/assets/non_existent_asset")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_05_cross_project_isolation(client, db_session):
    proj_a = Project(id="proj_a", name="Project A")
    scan_a = Scan(id="scan_a", project_id="proj_a", status=ScanStatus.COMPLETED, target_path="/tmp")
    asset_a = CryptoAsset(
        id="asset_in_a",
        scan_id="scan_a",
        name="Asset A",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        location="a.py"
    )

    proj_b = Project(id="proj_b", name="Project B")
    scan_b = Scan(id="scan_b", project_id="proj_b", status=ScanStatus.COMPLETED, target_path="/tmp")
    asset_b = CryptoAsset(
        id="asset_in_b",
        scan_id="scan_b",
        name="Asset B",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-128",
        purpose=CryptoPurpose.ENCRYPTION,
        location="b.py"
    )

    db_session.add_all([proj_a, scan_a, asset_a, proj_b, scan_b, asset_b])
    db_session.commit()

    # Attempt to request asset_in_b under proj_a path
    response = client.get("/api/v1/projects/proj_a/qars/assets/asset_in_b")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_06_empty_project_returns_zero_assets(client, db_session):
    proj = Project(id="proj_empty", name="Empty Project")
    db_session.add(proj)
    db_session.commit()

    response = client.get("/api/v1/projects/proj_empty/qars")
    assert response.status_code == 200
    data = response.json()

    assert data["project_id"] == "proj_empty"
    assert data["asset_count"] == 0
    assert data["assets"] == []
    assert data["summary"]["qars_average"] is None
    assert data["summary"]["qars_max"] is None
    assert data["summary"]["qars_min"] is None
    assert data["summary"]["critical_count"] == 0
    assert data["summary"]["high_count"] == 0
    assert data["summary"]["medium_count"] == 0
    assert data["summary"]["low_count"] == 0


def test_07_through_16_runtime_details_preserved(client, db_session):
    proj = Project(id="proj_qars_details", name="Details Proj")
    scan = Scan(id="scan_qars_details", project_id="proj_qars_details", status=ScanStatus.COMPLETED, target_path="/tmp")
    asset = CryptoAsset(
        id="asset_qars_details",
        scan_id="scan_qars_details",
        name="Detailed ECDSA Asset",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="ECDSA-P256",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        location="auth.py"
    )
    db_session.add_all([proj, scan, asset])
    db_session.commit()

    response = client.get("/api/v1/projects/proj_qars_details/qars/assets/asset_qars_details")
    assert response.status_code == 200
    data = response.json()["data"]

    # 7 & 8 & 9 & 10: Preserved IDs
    assert data["asset_id"] == "asset_qars_details"
    assert data["project_id"] == "proj_qars_details"
    assert data["scan_id"] == "scan_qars_details"

    # 11: Final QARS score returned
    assert "final_score" in data
    assert 0.0 <= data["final_score"] <= 100.0

    # 12: Component scores present
    assert data["algorithm_risk"] is not None
    assert data["availability"] is not None
    assert data["crypto_agility_evidence"] is not None
    assert data["migration_complexity"] is not None
    assert data["z_uncertainty"] is not None

    # 13: Provenance returned
    assert "provenance" in data
    assert "x_source" in data["provenance"]
    assert "z_source" in data["provenance"]

    # 14: Calibration versions returned
    assert "calibration_version" in data["algorithm_risk"]
    assert "calibration_version" in data["crypto_agility_evidence"]
    assert "calibration_version" in data["migration_complexity"]

    # 15: Missing evidence returned
    assert "missing_factors" in data["crypto_agility_evidence"]
    assert "missing_factors" in data["migration_complexity"]

    # 16: Explanation returned
    assert "explanation" in data
    assert "core_score" in data["explanation"]


def test_17_qars_validation_error_returns_422(client, db_session):
    proj = Project(id="proj_val_err", name="Validation Error Proj")
    scan = Scan(id="scan_val_err", project_id="proj_val_err", status=ScanStatus.COMPLETED, target_path="/tmp")
    asset = CryptoAsset(
        id="asset_val_err",
        scan_id="scan_val_err",
        name="Err Asset",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        location="err.py"
    )
    db_session.add_all([proj, scan, asset])
    db_session.commit()

    with patch("app.api.qars.evaluate_artifact_qars", side_effect=QARSValidationError("Invalid runtime input X")):
        response = client.get("/api/v1/projects/proj_val_err/qars/assets/asset_val_err")
        assert response.status_code == 422
        assert "Invalid runtime input X" in response.json()["detail"]


def test_18_unexpected_qars_failure_returns_500(client, db_session):
    proj = Project(id="proj_500_err", name="500 Error Proj")
    scan = Scan(id="scan_500_err", project_id="proj_500_err", status=ScanStatus.COMPLETED, target_path="/tmp")
    asset = CryptoAsset(
        id="asset_500_err",
        scan_id="scan_500_err",
        name="500 Asset",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        location="err.py"
    )
    db_session.add_all([proj, scan, asset])
    db_session.commit()

    with patch("app.api.qars.evaluate_artifact_qars", side_effect=Exception("Database unexpected crash")):
        response = client.get("/api/v1/projects/proj_500_err/qars/assets/asset_500_err")
        assert response.status_code == 500
        assert "Database unexpected crash" in response.json()["detail"]


def test_19_non_deadline_asset_returns_unconfigured_in_summary(client, db_session):
    proj = Project(id="proj_qars_aes", name="AES Proj")
    scan = Scan(id="scan_qars_aes", project_id="proj_qars_aes", status=ScanStatus.COMPLETED, target_path="/tmp")
    asset_rsa = CryptoAsset(
        id="asset_rsa",
        scan_id="scan_qars_aes",
        name="RSA Asset",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        location="rsa.py"
    )
    asset_aes = CryptoAsset(
        id="asset_aes",
        scan_id="scan_qars_aes",
        name="AES Asset",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256",
        purpose=CryptoPurpose.ENCRYPTION,
        location="aes.py"
    )
    db_session.add_all([proj, scan, asset_rsa, asset_aes])
    db_session.commit()

    response = client.get("/api/v1/projects/proj_qars_aes/qars")
    assert response.status_code == 200
    data = response.json()
    assert data["asset_count"] == 2
    summary = data["summary"]
    assert summary["unconfigured_count"] == 1
    assert summary["qars_average"] is not None
