import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from app.main import app
from app.core.database import get_db, Base
from app.models.db_models import Project, Scan, CryptoAsset, AuditEvent, RiskAssessment
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety
from app.services.business_criticality_service import BusinessCriticalityService
from app.risk.service import RiskService
from app.prioritization.service import PrioritizationService
from app.migration.planner import MigrationPlanner

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

def test_calculate_wis_em_scores(db_session):
    # Tests 3 & 4: WIS, EM, normalized score and label assignment
    service = BusinessCriticalityService(db_session)
    ratings = {
        "dataSensitivity": 5,
        "dataShelfLife": 5,
        "confidentialityImpact": 5,
        "integrityImpact": 5,
        "availabilityImpact": 5,
        "regulatoryExposure": 5,
        "financialImpact": 5,
        "reputationalImpact": 5,
        "exposureRating": 4,
    }
    res = service.calculate_scores(ratings)
    assert res["wis"] == 5.0
    assert res["exposure_multiplier"] == 1.375
    assert res["normalized_score"] == 4.58
    assert res["calculated_label"] == "CRITICAL"

def test_get_and_save_business_criticality(db_session):
    # Tests 1 & 2: Load and save factor ratings
    proj = Project(id="proj-bc-1", name="BC Test Project")
    db_session.add(proj)
    db_session.commit()

    service = BusinessCriticalityService(db_session)
    data = service.get_project_business_criticality(proj.id)
    assert data["project_id"] == proj.id
    assert data["is_overridden"] is False

    updated = service.update_project_business_criticality(
        project_id=proj.id,
        factor_ratings={"dataSensitivity": 2, "exposureRating": 1}
    )
    assert updated["factor_ratings"]["dataSensitivity"] == 2
    assert updated["factor_ratings"]["exposureRating"] == 1

def test_override_requires_nonempty_reason(db_session):
    # Test 7: Override requires reason
    proj = Project(id="proj-bc-reason", name="Reason Project")
    db_session.add(proj)
    db_session.commit()

    service = BusinessCriticalityService(db_session)
    with pytest.raises(ValueError) as exc_info:
        service.update_project_business_criticality(
            project_id=proj.id,
            user_override="CRITICAL",
            adjustment_reason="   "  # Empty whitespace
        )
    assert "Adjustment reason is required" in str(exc_info.value)

def test_override_and_revert_flow(db_session):
    # Tests 6, 8, 21, 22, 23: Override, Revert, and Audit creation
    proj = Project(id="proj-ov-rev", name="Override Revert Project")
    db_session.add(proj)
    db_session.commit()

    service = BusinessCriticalityService(db_session)
    # 1. Override to CRITICAL
    overridden = service.update_project_business_criticality(
        project_id=proj.id,
        user_override="CRITICAL",
        adjustment_reason="Contractual SLA compliance requirements"
    )
    assert overridden["effective_criticality"] == "CRITICAL"
    assert overridden["is_overridden"] is True

    # Audit event logged
    events = db_session.query(AuditEvent).filter(AuditEvent.project_id == proj.id).all()
    assert len(events) == 1
    assert events[0].action == "BUSINESS_CRITICALITY_OVERRIDE"
    assert events[0].details["user_override"] == "CRITICAL"
    assert events[0].details["reason"] == "Contractual SLA compliance requirements"

    # 2. Revert override
    reverted = service.update_project_business_criticality(
        project_id=proj.id,
        revert_override=True
    )
    assert reverted["effective_criticality"] == overridden["system_criticality"]
    assert reverted["is_overridden"] is False

    events2 = db_session.query(AuditEvent).filter(AuditEvent.project_id == proj.id).all()
    assert len(events2) == 2
    assert events2[1].action == "BUSINESS_CRITICALITY_OVERRIDE_REVERTED"

def test_effective_criticality_influences_risk_and_priority(db_session):
    # Tests 9, 10, 11, 14, 15, 16: Risk & Priority change on override
    proj = Project(id="proj-rp", name="Risk Priority Project")
    scan = Scan(id="scan-rp", project_id=proj.id, target_path="/tmp/test", status=ScanStatus.COMPLETED)
    asset = CryptoAsset(
        id="asset-rp-1",
        scan_id=scan.id,
        name="AES key",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES",
        key_size=128,
        purpose=CryptoPurpose.ENCRYPTION,
        location="main.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db_session.add_all([proj, scan, asset])
    db_session.commit()

    risk_service = RiskService(db_session)
    risk_service.assess_project(proj.id)

    prioritization_service = PrioritizationService(db_session)
    p_queue_before = prioritization_service.get_prioritized_queue(proj.id)
    assert len(p_queue_before.prioritized_queue) == 1

    # Override criticality to CRITICAL
    bc_service = BusinessCriticalityService(db_session)
    bc_service.update_project_business_criticality(
        project_id=proj.id,
        user_override="CRITICAL",
        adjustment_reason="Payment processing gateway"
    )

    p_queue_after = prioritization_service.get_prioritized_queue(proj.id)
    assert len(p_queue_after.prioritized_queue) == 1
    item_after = p_queue_after.prioritized_queue[0]
    assert item_after.business_context.effective_planning_criticality == "CRITICAL"
    assert item_after.business_context.is_user_adjusted is True
    assert item_after.business_context.adjustment_reason == "Payment processing gateway"

def test_roadmap_uses_actual_effective_criticality(db_session, tmp_path):
    # Tests 17, 18, 19, 20: Migration planner uses effective criticality instead of hardcoded 80.0
    test_dir = tmp_path / "src"
    test_dir.mkdir()
    (test_dir / "sample.py").write_text("from cryptography.hazmat.primitives.asymmetric import rsa\n")

    proj = Project(id="proj-road", name="Roadmap Project")
    scan = Scan(id="scan-road", project_id=proj.id, target_path=str(test_dir), status=ScanStatus.COMPLETED)
    asset = CryptoAsset(
        id="asset-road-1",
        scan_id=scan.id,
        name="RSA key",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        key_size=2048,
        purpose=CryptoPurpose.ENCRYPTION,
        location="sample.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db_session.add_all([proj, scan, asset])
    db_session.commit()

    # Set user override to LOW
    bc_service = BusinessCriticalityService(db_session)
    bc_service.update_project_business_criticality(
        project_id=proj.id,
        user_override="LOW",
        adjustment_reason="Internal non-production component"
    )

    planner = MigrationPlanner()
    plan = planner.create_plan_for_project(db_session, proj.id, "LOW Criticality Plan", [asset])

    assert plan is not None
    assert plan.total_person_days > 0.0

def test_audit_endpoint_functional(client, db_session):
    # Test 24: Read-only audit endpoint
    proj = Project(id="proj-audit-ep", name="Audit Endpoint Project")
    db_session.add(proj)
    db_session.commit()

    bc_service = BusinessCriticalityService(db_session)
    bc_service.update_project_business_criticality(
        project_id=proj.id,
        user_override="HIGH",
        adjustment_reason="Core auth service"
    )

    resp = client.get(f"/api/v1/projects/{proj.id}/audit")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 1
    assert events[0]["action"] == "BUSINESS_CRITICALITY_OVERRIDE"
