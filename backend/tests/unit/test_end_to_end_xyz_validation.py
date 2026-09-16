import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.engines.x_engine import XEngine
from app.engines.y_engine import YEngine
from app.engines.z_engine import ZEngine
from app.engines.mosca_engine import MoscaEngine
from app.models.schemas import CryptoAssetResponse, RiskAssessRequest


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_j1_user_x_supplied():
    engine = XEngine()
    res = engine.evaluate_x(user_x_years=15)
    assert res["value_years"] == 15.0
    assert res["value"] == 15
    assert res["source"] == "USER"


def test_j2_domain_x_baseline():
    engine = XEngine()
    res = engine.evaluate_x(user_domain="banking_finance")
    assert res["value_years"] == 15.0
    assert res["source"] == "DOMAIN_BASELINE"


def test_j3_system_default_x():
    engine = XEngine()
    res = engine.evaluate_x()
    assert res["value_years"] == 20.0
    assert res["source"] == "SYSTEM_DEFAULT"


def test_j4_y_fast_scenario():
    engine = YEngine()
    res = engine.evaluate_y("FAST")
    assert res["value_years"] == 5.0
    assert res["scenario"] == "FAST"
    assert res["source"] == "USER_SELECTED"


def test_j5_y_standard_scenario():
    engine = YEngine()
    res = engine.evaluate_y("STANDARD")
    assert res["value_years"] == 10.0
    assert res["scenario"] == "STANDARD"
    assert res["source"] == "USER_SELECTED"


def test_j6_y_legacy_heavy_scenario():
    engine = YEngine()
    res = engine.evaluate_y("LEGACY_HEAVY")
    assert res["value_years"] == 20.0
    assert res["scenario"] == "LEGACY_HEAVY"
    assert res["source"] == "USER_SELECTED"


def test_j7_different_primitive_types_z_base_scores():
    z_engine = ZEngine()

    aes_res = z_engine.evaluate_component({"primitive": "AES", "algorithm_name": "AES-256-GCM"})
    assert aes_res["base_score"] == 1.0

    ecdsa_res = z_engine.evaluate_component({"primitive": "ECDSA", "algorithm_name": "ECDSA-P256"})
    assert ecdsa_res["base_score"] == 4.0

    rsa_res = z_engine.evaluate_component({"primitive": "RSA", "algorithm_name": "RSA-2048"})
    assert rsa_res["base_score"] == 5.0


def test_j8_different_environments_multiplier():
    z_engine = ZEngine()

    soft_res = z_engine.evaluate_component({"primitive": "RSA", "execution_environment": "SOFTWARE"})
    assert soft_res["env_multiplier"] == 1.0

    onprem_res = z_engine.evaluate_component({"primitive": "RSA", "execution_environment": "ON_PREM"})
    assert onprem_res["env_multiplier"] == 2.0

    hsm_res = z_engine.evaluate_component({"primitive": "RSA", "execution_environment": "HARDWARE"})
    assert hsm_res["env_multiplier"] == 3.0

    embed_res = z_engine.evaluate_component({"primitive": "RSA", "execution_environment": "EMBEDDED"})
    assert embed_res["env_multiplier"] == 4.0


def test_j9_different_crypto_ref_array_counts():
    z_engine = ZEngine()

    ref0_res = z_engine.evaluate_component({"primitive": "RSA", "cryptoRefArray": []})
    assert ref0_res["dep_factor"] == 1.0

    ref3_res = z_engine.evaluate_component({"primitive": "RSA", "cryptoRefArray": ["r1", "r2", "r3"]})
    assert ref3_res["dep_factor"] == 1.3


def test_j10_mosca_uses_canonical_xyz_calculation():
    mosca = MoscaEngine()

    comp = {"primitive": "RSA", "algorithm_name": "RSA-2048"}
    res = mosca.evaluate_component_mosca(component=comp, user_x_years=20, user_y_scenario="STANDARD")

    assert res["x"]["value_years"] == 20.0
    assert res["y"]["value_years"] == 10.0
    assert res["z"]["z_planning_horizon_years"] in (10, 10.0, 15, 15.0)
    assert res["mosca_score"] == 20.0  # 20 + 10 - 10 = 20
    assert res["mosca_score_years"] == 20.0


def test_j11_crypto_asset_response_no_manufactured_defaults():
    asset_dict = {
        "id": "ast-101",
        "scan_id": "scn-101",
        "name": "RSA Signer",
        "asset_type": "ALGORITHM",
        "algorithm_name": "RSA-2048",
        "purpose": "SIGNATURE",
        "location": "src/auth.py",
        "quantum_safety": "QUANTUM_VULNERABLE",
        "created_at": "2026-09-10T08:00:00Z"
    }
    resp = CryptoAssetResponse(**asset_dict)
    assert resp.data_lifetime_years is None
    assert resp.migration_time_years is None
    assert resp.quantum_threat_horizon is None

    req = RiskAssessRequest(asset_id="ast-101")
    assert req.data_lifetime_years is None
    assert req.migration_time_years is None
    assert req.quantum_threat_horizon_year is None


def test_k1_four_primitive_integration():
    """
    Test 4 canonical primitive types:
    1. RSA-2048 (Shor-vulnerable public key)
    2. ECDSA-P256 (Shor-vulnerable signature)
    3. AES-256 (Symmetric cipher)
    4. ML-KEM-768 (PQC primitive)
    """
    mosca = MoscaEngine()

    # 1. RSA-2048
    rsa_comp = {"id": "c1", "primitive": "RSA", "algorithm_name": "RSA-2048", "purpose": "KEY_ESTABLISHMENT"}
    rsa_res = mosca.evaluate_component_mosca(component=rsa_comp, user_x_years=10, user_y_scenario="STANDARD")
    assert rsa_res["z"]["z_value"] == 10.0
    assert rsa_res["mosca_score"] == 10.0  # 10 + 10 - 10 = 10
    assert rsa_res["technical_urgency"] in ("CRITICAL", "HIGH")
    assert "Shor's algorithm" in rsa_res["z"]["explanation"] or "asymmetric" in rsa_res["z"]["explanation"]

    # 2. ECDSA-P256
    ecdsa_comp = {"id": "c2", "primitive": "ECDSA", "algorithm_name": "ECDSA-P256", "purpose": "SIGNATURE"}
    ecdsa_res = mosca.evaluate_component_mosca(component=ecdsa_comp, user_x_years=10, user_y_scenario="STANDARD")
    assert ecdsa_res["z"]["z_value"] == 10.0
    assert ecdsa_res["mosca_score"] == 10.0  # 10 + 10 - 10 = 10
    assert ecdsa_res["technical_urgency"] in ("CRITICAL", "HIGH")

    # 3. AES-256
    aes_comp = {"id": "c3", "primitive": "AES", "algorithm_name": "AES-256-GCM", "purpose": "SYMMETRIC_ENCRYPTION"}
    aes_res = mosca.evaluate_component_mosca(component=aes_comp, user_x_years=10, user_y_scenario="STANDARD")
    assert aes_res["z"]["z_value"] is None
    assert aes_res["mosca_score"] is None
    assert aes_res["z"]["status"] == "REDUCED_BUT_ACCEPTABLE"
    assert "Grover" in aes_res["z"]["explanation"] or "symmetric" in aes_res["z"]["explanation"]

    # 4. ML-KEM-768
    mlkem_comp = {"id": "c4", "primitive": "ML-KEM", "algorithm_name": "ML-KEM-768", "purpose": "KEY_ESTABLISHMENT"}
    mlkem_res = mosca.evaluate_component_mosca(component=mlkem_comp, user_x_years=10, user_y_scenario="STANDARD")
    assert mlkem_res["z"]["z_value"] is None
    assert mlkem_res["mosca_score"] is None
    assert mlkem_res["z"]["status"] == "NO_IMMEDIATE_QUANTUM_DEADLINE"
    assert "Post-quantum" in mlkem_res["z"]["explanation"] or "PQC" in mlkem_res["z"]["explanation"]
