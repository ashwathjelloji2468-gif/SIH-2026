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

def test_risk_assessment_success_path(client, db_session):
    proj = Project(id="proj_risk_test", name="Risk Test Proj")
    scan = Scan(id="scan_risk_test", project_id="proj_risk_test", status=ScanStatus.COMPLETED, target_path="/tmp")
    asset = CryptoAsset(
        id="asset_risk_test",
        scan_id="scan_risk_test",
        name="Test RSA Asset",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        location="app.py"
    )
    db_session.add_all([proj, scan, asset])
    db_session.commit()

    response = client.post("/api/v1/projects/proj_risk_test/risk/assess", json={})
    assert response.status_code in [200, 201]
    data = response.json()
    assert isinstance(data, list)

def test_risk_assessment_unexpected_exception_returns_500(client, db_session):
    proj = Project(id="proj_risk_err", name="Risk Err Proj")
    db_session.add(proj)
    db_session.commit()

    with patch("app.risk.service.RiskService.assess_project", side_effect=Exception("test failure")):
        response = client.post("/api/v1/projects/proj_risk_err/risk/assess", json={})
        assert response.status_code == 500
        data = response.json()
        assert data == {
            "detail": "Risk assessment execution failed.",
            "error_code": "RISK_ASSESSMENT_EXECUTION_ERROR"
        }
        assert "traceback" not in data
        assert "test failure" not in str(data)
