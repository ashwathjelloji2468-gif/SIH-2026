import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.db_models import Project, Scan, CryptoAsset, RiskAssessment
from app.repositories.project_repository import ProjectRepository
from app.repositories.asset_repository import AssetRepository
from app.risk.service import RiskService
from app.engines.x_engine import XEngine
from app.engines.y_engine import YEngine
from app.engines.z_engine import ZEngine
from app.engines.mosca_engine import MoscaEngine
from app.models.schemas import CryptoAssetResponse, RiskAssessRequest
from app.models.enums import QuantumSafety, CryptoPurpose, AssetType


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed test project and scan
    proj = Project(
        id="proj-p1-test",
        name="P1 Verification Project",
        user_x_years=15,
        user_domain="banking_finance",
        user_y_scenario="COMPLEX"
    )
    session.add(proj)

    scan = Scan(
        id="scan-p1-test",
        project_id="proj-p1-test",
        status="COMPLETED",
        target_path="/app",
        scan_type="source",
        cbom_version="1.6"
    )
    session.add(scan)

    rsa_asset = CryptoAsset(
        id="ast-rsa-2048",
        scan_id="scan-p1-test",
        name="RSA Core Key",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        location="src/crypto/rsa.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    session.add(rsa_asset)

    ecdsa_asset = CryptoAsset(
        id="ast-ecdsa-256",
        scan_id="scan-p1-test",
        name="ECDSA Auth Signer",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="ECDSA-P256",
        purpose=CryptoPurpose.SIGNATURE,
        location="src/auth/signer.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    session.add(ecdsa_asset)

    aes_asset = CryptoAsset(
        id="ast-aes-256",
        scan_id="scan-p1-test",
        name="AES Vault Encryption",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256-GCM",
        purpose=CryptoPurpose.ENCRYPTION,
        location="src/storage/vault.py",
        quantum_safety=QuantumSafety.NOT_DIRECTLY_QUANTUM_VULNERABLE
    )
    session.add(aes_asset)

    mlkem_asset = CryptoAsset(
        id="ast-mlkem-768",
        scan_id="scan-p1-test",
        name="PQC Hybrid KEM",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="ML-KEM-768",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        location="src/pqc/kem.py",
        quantum_safety=QuantumSafety.QUANTUM_SAFE
    )
    session.add(mlkem_asset)

    session.commit()
    yield session
    session.close()


def test_1_business_criticality_risk_refresh(db_session):
    service = RiskService(db_session)

    # Initial assessment with MEDIUM criticality
    res1 = service.assess_asset("ast-rsa-2048", business_criticality_label="MEDIUM")
    score1 = res1["risk_score"]

    # Update business criticality to CRITICAL
    res2 = service.assess_asset("ast-rsa-2048", business_criticality_label="CRITICAL", force_reassessment=True)
    score2 = res2["risk_score"]

    # Re-assessed risk score must increase with higher criticality label
    assert score2 > score1
    assert res2["factors"]["business_criticality"] == 100.0


def test_2_xyz_surface_identicality(db_session):
    service = RiskService(db_session)
    res = service.assess_asset("ast-rsa-2048")

    x_val = res["x"]["value_years"]
    y_val = res["y"]["value_years"]
    z_val = res["z"]["z_planning_horizon_years"]
    mosca_score = res["mosca_score"]

    # Verify identical values are present at top-level and nested mosca dict
    assert res["mosca"]["x_years"] == x_val
    assert res["mosca"]["y_years"] == y_val
    assert res["mosca"]["z_horizon_years"] == z_val
    assert res["mosca"]["mosca_score"] == mosca_score


def test_3_no_hidden_fallback_numbers():
    # Schema defaults must be None
    resp = CryptoAssetResponse(
        id="a1", scan_id="s1", name="Test", asset_type=AssetType.ALGORITHM,
        algorithm_name="AES", purpose=CryptoPurpose.ENCRYPTION,
        location="loc", quantum_safety=QuantumSafety.NOT_DIRECTLY_QUANTUM_VULNERABLE
    )
    assert resp.data_lifetime_years is None
    assert resp.migration_time_years is None
    assert resp.quantum_threat_horizon is None

    req = RiskAssessRequest(asset_id="a1")
    assert req.data_lifetime_years is None
    assert req.migration_time_years is None
    assert req.quantum_threat_horizon_year is None


def test_4_rsa_risk_explanation_correctness():
    z_engine = ZEngine()
    rsa_res = z_engine.evaluate_component({
        "primitive": "RSA",
        "algorithm_name": "RSA-2048",
        "purpose": "KEY_ESTABLISHMENT"
    })

    explanation = rsa_res["explanation"]

    # Must be public key / asymmetric / Shor's algorithm
    assert rsa_res["quantum_class"] in ("shor_vulnerable_public_key", "SHOR_VULNERABLE")
    assert "Shor's algorithm" in explanation or "asymmetric" in explanation or "public-key" in explanation.lower()

    # Must NOT describe RSA as symmetric nor claim Grover search protection
    assert "symmetric cipher" not in explanation.lower()
    assert "grover search" not in explanation.lower()


def test_5_threat_horizon_semantics():
    z_engine = ZEngine()
    res = z_engine.evaluate_component({
        "primitive": "RSA",
        "algorithm_name": "RSA-2048"
    })

    # Distinguish relative years vs target year vs assumption wording
    assert "z_planning_horizon_years" in res
    assert "z_target_year" in res
    assert res["z_target_year"] == 2026 + int(res["z_value"])
    assert "quantum deadline" in res["explanation"].lower() or "threat horizon" in res["explanation"].lower() or "planning" in res["explanation"].lower()


def test_6_refresh_persistence_test(db_session):
    # Verify project-level X, Y, Z settings persist and are used
    proj_repo = ProjectRepository(db_session)
    proj = proj_repo.get("proj-p1-test")

    assert proj.user_x_years == 15
    assert proj.user_domain == "banking_finance"
    assert proj.user_y_scenario == "COMPLEX"

    # Evaluate project with MoscaEngine
    mosca = MoscaEngine()
    asset_repo = AssetRepository(db_session)
    assets = asset_repo.get_by_project("proj-p1-test")
    p_res = mosca.evaluate_project_mosca(proj, assets)

    # All components in project inherit project's X=15 and Y=15 (COMPLEX scenario)
    for comp in p_res["components"]:
        assert comp["x"]["value_years"] == 15.0
        assert comp["y"]["value_years"] == 15.0


def test_7_api_source_of_truth_test(db_session):
    service = RiskService(db_session)
    res = service.assess_asset("ast-rsa-2048")

    # Trace back to canonical MoscaEngine
    m_engine = MoscaEngine()
    comp_dict = {
        "id": "ast-rsa-2048",
        "primitive": "RSA",
        "algorithm_name": "RSA-2048",
        "purpose": "KEY_ESTABLISHMENT",
        "location": "src/crypto/rsa.py"
    }
    m_eval = m_engine.evaluate_component_mosca(comp_dict, user_x_years=15, user_y_scenario="COMPLEX")

    assert res["mosca_score"] == m_eval["mosca_score"]
    assert res["technical_urgency"] == m_eval["technical_urgency"]


def test_8_invalid_missing_data_representation():
    z_engine = ZEngine()

    # Unclassified / non-standard asset
    unclassified_res = z_engine.evaluate_component({
        "primitive": "UNKNOWN_CUSTOM_PRIMITIVE",
        "algorithm_name": "UNKNOWN_CUSTOM_PRIMITIVE"
    })

    # Must return REQUIRES_REVIEW with z_value None
    assert unclassified_res["status"] == "REQUIRES_REVIEW"
    assert unclassified_res["z_value"] is None


def test_9_cross_asset_evaluation_diversity(db_session):
    service = RiskService(db_session)
    results = service.assess_project("proj-p1-test")

    # Map by algorithm
    by_alg = {r["algorithm_name"]: r for r in results}

    # 1. RSA-2048
    rsa = by_alg["RSA-2048"]
    assert rsa["quantum_status"] == "QUANTUM_VULNERABLE"
    assert rsa["mosca_score"] is not None

    # 2. ECDSA-P256
    ecdsa = by_alg["ECDSA-P256"]
    assert ecdsa["quantum_status"] == "QUANTUM_VULNERABLE"
    assert ecdsa["mosca_score"] is not None

    # 3. AES-256-GCM
    aes = by_alg["AES-256-GCM"]
    assert aes["mosca"]["z_horizon_years"] is None or aes["mosca_score"] is None or aes["technical_urgency"] == "LOW"

    # 4. ML-KEM-768
    mlkem = by_alg["ML-KEM-768"]
    assert mlkem["technical_urgency"] == "LOW"
    assert mlkem["mosca"]["z_horizon_years"] is None
