import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.db_models import (
    Project, Scan, CryptoAsset, RiskAssessment, Recommendation, BlastRadiusResult, AuditEvent
)
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety, RiskLevel, RecommendationCategory

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base

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
    def override_get_db():
        try:
            yield session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield session
    finally:
        session.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)

client = TestClient(app)

@pytest.fixture
def setup_reporting_fixture(db_session: Session):
    """
    Sets up a deterministic fixture project and scan for Priority 8 report verification tests.
    """
    project = Project(
        name="Report Verification Test System",
        description="Core banking cryptographic infrastructure",
        repository_url="https://github.com/sentriq/core-banking.git",
        default_migration_profile="SECURITY_FIRST",
        business_context={
            "data_sensitivity": 5,
            "operational_criticality": 5,
            "user_override": "CRITICAL",
            "override_reason": "PCI-DSS 4.0 Compliance Requirement"
        }
    )
    db_session.add(project)
    db_session.flush()

    scan = Scan(
        project_id=project.id,
        status=ScanStatus.COMPLETED,
        target_path="/src/crypto",
        scan_type="source",
        created_at=datetime(2026, 9, 15, 10, 0, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 9, 15, 10, 5, 0, tzinfo=timezone.utc),
        cbom_json={
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "serialNumber": "urn:uuid:11111111-2222-3333-4444-555555555555",
            "version": 1,
            "metadata": {
                "timestamp": "2026-09-15T10:05:00Z",
                "component": {
                    "name": "Report Verification Test System",
                    "type": "application"
                }
            },
            "components": [
                {
                    "type": "crypto-asset",
                    "name": "RSA-2048 Core Key",
                    "cryptoProperties": {
                        "assetType": "algorithm",
                        "algorithmProperties": {
                            "primitive": "RSA",
                            "variant": "2048"
                        }
                    }
                },
                {
                    "type": "crypto-asset",
                    "name": "AES-256 Storage Cipher",
                    "cryptoProperties": {
                        "assetType": "algorithm",
                        "algorithmProperties": {
                            "primitive": "AES",
                            "variant": "256-GCM"
                        }
                    }
                }
            ]
        }
    )
    db_session.add(scan)
    db_session.flush()

    asset1 = CryptoAsset(
        scan_id=scan.id,
        name="RSA-2048 Core Key",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        key_size=2048,
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        location="backend/app/auth/key_exchange.py",
        line_number=42,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    asset2 = CryptoAsset(
        scan_id=scan.id,
        name="AES-256 Storage Cipher",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256-GCM",
        key_size=256,
        purpose=CryptoPurpose.ENCRYPTION,
        location="backend/app/db/cipher.py",
        line_number=18,
        quantum_safety=QuantumSafety.QUANTUM_SAFE
    )
    db_session.add_all([asset1, asset2])
    db_session.flush()

    ra1 = RiskAssessment(
        asset_id=asset1.id,
        risk_score=85.0,
        risk_level=RiskLevel.CRITICAL,
        explanation="Legacy RSA-2048 vulnerable to Shor's algorithm"
    )
    ra2 = RiskAssessment(
        asset_id=asset2.id,
        risk_score=15.0,
        risk_level=RiskLevel.LOW,
        explanation="Symmetric AES-256 is quantum resistant"
    )
    db_session.add_all([ra1, ra2])

    rec1 = Recommendation(
        asset_id=asset1.id,
        target_pqc_candidate="ML-KEM-768",
        recommended_algorithm="ML-KEM-768 (FIPS 203)",
        category=RecommendationCategory.PQC_REPLACEMENT,
        priority="CRITICAL",
        rationale="Migrate RSA-2048 key exchange to NIST FIPS 203 ML-KEM-768"
    )
    db_session.add(rec1)

    br = BlastRadiusResult(
        scan_id=scan.id,
        root_node_id=asset1.id,
        radius_score=88.5,
        affected_nodes_count=5,
        systems_count=2,
        data_classes=["AUTHENTICATION_CREDENTIALS", "FINANCIAL_RECORDS"],
        estimated_migration_effort=12.0
    )
    db_session.add(br)

    db_session.commit()
    return project, scan, asset1, asset2


def test_cbom_json_uses_actual_scan_cbom(setup_reporting_fixture):
    """Test that CBOM JSON export returns exact persisted Scan.cbom_json."""
    project, scan, asset1, asset2 = setup_reporting_fixture

    resp = client.get(f"/api/v1/scans/{scan.id}/cbom")
    assert resp.status_code == 200
    cbom_data = resp.json()

    assert cbom_data["bomFormat"] == "CycloneDX"
    assert cbom_data["specVersion"] == "1.6"
    assert len(cbom_data["components"]) == 2
    assert cbom_data["components"][0]["name"] == "RSA-2048 Core Key"


def test_missing_cbom_returns_honest_error(db_session: Session):
    """Test that requesting CBOM for a scan with missing cbom_json returns honest error."""
    proj = Project(name="Empty Scan Project")
    db_session.add(proj)
    db_session.flush()

    empty_scan = Scan(project_id=proj.id, status=ScanStatus.QUEUED, target_path="/tmp/empty", cbom_json=None)
    db_session.add(empty_scan)
    db_session.commit()

    resp = client.get(f"/api/v1/scans/{empty_scan.id}/cbom")
    assert resp.status_code == 404
    assert "CBOM_NOT_AVAILABLE" in resp.json()["detail"]


def test_cbom_pdf_generated_from_same_cbom_data(setup_reporting_fixture):
    """Test that CBOM PDF is generated from the same canonical Scan.cbom_json."""
    project, scan, asset1, asset2 = setup_reporting_fixture

    resp = client.get(f"/api/v1/scans/{scan.id}/cbom/pdf")
    assert resp.status_code == 200
    pdf_report = resp.json()

    assert pdf_report["report_type"] == "CBOM_PDF"
    assert pdf_report["specVersion"] == "1.6"
    assert pdf_report["components_count"] == 2
    assert "CycloneDX" in pdf_report["report_html"]
    assert "RSA-2048 Core Key" in pdf_report["report_html"]


def test_mismatched_project_and_scan_rejected(setup_reporting_fixture, db_session: Session):
    """Test that requesting a report with mismatched project_id and scan_id is rejected."""
    project_a, scan_a, _, _ = setup_reporting_fixture

    project_b = Project(name="Project B")
    db_session.add(project_b)
    db_session.flush()

    scan_b = Scan(project_id=project_b.id, status=ScanStatus.COMPLETED, target_path="/tmp/b")
    db_session.add(scan_b)
    db_session.commit()

    # Request report for Project A passing Scan B (which belongs to Project B)
    resp = client.get(f"/api/v1/projects/{project_a.id}/reports/executive?scan_id={scan_b.id}")
    assert resp.status_code == 400
    assert "does not belong to project" in resp.json()["detail"]


def test_risk_report_uses_actual_persisted_data(setup_reporting_fixture):
    """Test that Risk Report uses actual persisted RiskAssessments, effective criticality, and blast radius."""
    project, scan, asset1, asset2 = setup_reporting_fixture

    resp = client.get(f"/api/v1/projects/{project.id}/reports/risk?scan_id={scan.id}")
    assert resp.status_code == 200
    report = resp.json()

    assert report["report_type"] == "RISK"
    assert report["project_name"] == "Report Verification Test System"
    assert report["scan_id"] == scan.id
    assert report["business_criticality"]["effective_criticality"] == "CRITICAL"
    assert report["business_criticality"]["user_override"] == "CRITICAL"
    assert "PCI-DSS 4.0 Compliance Requirement" in report["business_criticality"]["override_reason"]

    # Verify HTML contents reflect real data
    html = report["report_html"]
    assert "RSA-2048" in html
    assert "key_exchange.py" in html
    assert "CRITICAL" in html
    assert "Blast Radius Analysis" in html or "Blast Radius" in html
    assert report["blast_radius_results"] is not None


def test_executive_report_reflects_real_data(setup_reporting_fixture):
    """Test that Executive Report reflects real project state and metadata."""
    project, scan, asset1, asset2 = setup_reporting_fixture

    resp = client.get(f"/api/v1/projects/{project.id}/reports/executive?scan_id={scan.id}")
    assert resp.status_code == 200
    report = resp.json()

    assert report["report_type"] == "EXECUTIVE"
    assert report["total_assets"] == 2
    assert report["vulnerable_assets"] == 1
    assert report["business_criticality"]["effective_criticality"] == "CRITICAL"

    html = report["report_html"]
    assert "Report Verification Test System" in html
    assert "ML-KEM-768" in html or "ML-KEM" in html


def test_cross_report_consistency(setup_reporting_fixture):
    """
    Cross-Report Consistency Test: Verify CBOM JSON, CBOM PDF, Risk Report, and Executive Report
    all agree on shared facts for the same project/scan.
    """
    project, scan, asset1, asset2 = setup_reporting_fixture

    # 1. Fetch CBOM JSON
    res_cbom = client.get(f"/api/v1/scans/{scan.id}/cbom").json()
    # 2. Fetch CBOM PDF
    res_pdf = client.get(f"/api/v1/scans/{scan.id}/cbom/pdf").json()
    # 3. Fetch Risk Report
    res_risk = client.get(f"/api/v1/projects/{project.id}/reports/risk?scan_id={scan.id}").json()
    # 4. Fetch Executive Report
    res_exec = client.get(f"/api/v1/projects/{project.id}/reports/executive?scan_id={scan.id}").json()

    # Shared Facts Assertions across all 4 reports
    cbom_components_count = len(res_cbom["components"])
    pdf_components_count = res_pdf["components_count"]
    risk_assets_count = len(res_risk["risk_summary"]["priority_list"]) if "priority_list" in res_risk["risk_summary"] else 2
    exec_assets_count = res_exec["total_assets"]

    assert cbom_components_count == 2
    assert pdf_components_count == 2
    assert exec_assets_count == 2

    # Verify project name consistency
    assert res_pdf["project_name"] == project.name
    assert res_risk["project_name"] == project.name
    assert res_exec["project_name"] == project.name

    # Verify scan ID consistency
    assert res_pdf["scan_id"] == scan.id
    assert res_risk["scan_id"] == scan.id
    assert res_exec["scan_id"] == scan.id

    # Verify Business Criticality consistency between Risk & Executive Report
    assert res_risk["business_criticality"]["effective_criticality"] == "CRITICAL"
    assert res_exec["business_criticality"]["effective_criticality"] == "CRITICAL"
