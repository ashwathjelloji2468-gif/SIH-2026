import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.db_models import Project, Scan, CryptoAsset
from app.engines.x_engine import XEngine
from app.engines.y_engine import YEngine
from app.engines.z_engine import ZEngine
from app.engines.mosca_engine import MoscaEngine
from app.repositories.project_repository import ProjectRepository
from app.repositories.asset_repository import AssetRepository
from app.risk.service import RiskService
from app.models.schemas import CryptoAssetResponse, ProjectCreate, ProjectResponse


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_1_user_x_supplied():
    engine = XEngine()
    res = engine.evaluate_x(user_x_years=15)
    assert res["value"] == 15
    assert res["source"] == "USER"


def test_2_domain_x_baseline():
    engine = XEngine()
    res = engine.evaluate_x(user_domain="banking_finance")
    assert res["value"] == 15
    assert res["source"] == "DOMAIN_BASELINE"


def test_3_system_default_x():
    engine = XEngine()
    res = engine.evaluate_x()
    assert res["value"] == 20
    assert res["source"] == "SYSTEM_DEFAULT"


def test_4_y_fast_scenario():
    engine = YEngine()
    res = engine.evaluate_y("FAST")
    assert res["value"] == 5
    assert res["scenario"] == "FAST"
    assert res["source"] == "USER_SELECTED"


def test_5_y_standard_scenario():
    engine = YEngine()
    res = engine.evaluate_y("STANDARD")
    assert res["value"] == 10
    assert res["scenario"] == "STANDARD"
    assert res["source"] == "USER_SELECTED"


def test_6_y_legacy_heavy_scenario():
    engine = YEngine()
    res = engine.evaluate_y("LEGACY_HEAVY")
    assert res["value"] == 20
    assert res["scenario"] == "LEGACY_HEAVY"
    assert res["source"] == "USER_SELECTED"


def test_7_different_primitive_types_z_base_scores():
    z_engine = ZEngine()

    # Hash / Symmetric -> base 1.0
    aes_res = z_engine.evaluate_component({"primitive": "AES", "algorithm_name": "AES-256-GCM"})
    assert aes_res["base_score"] == 1.0

    # Signature -> base 4.0
    ecdsa_res = z_engine.evaluate_component({"primitive": "ECDSA", "algorithm_name": "ECDSA-P256"})
    assert ecdsa_res["base_score"] == 4.0

    # Key Exchange / Asymmetric / Cert -> base 5.0
    rsa_res = z_engine.evaluate_component({"primitive": "RSA", "algorithm_name": "RSA-2048"})
    assert rsa_res["base_score"] == 5.0


def test_8_different_environments_multiplier():
    z_engine = ZEngine()

    # Software env -> mult 1.0
    soft_res = z_engine.evaluate_component({"primitive": "RSA", "execution_environment": "SOFTWARE"})
    assert soft_res["env_multiplier"] == 1.0
    assert soft_res["z_score"] == 5.0  # 5 * 1 * 1

    # On-Prem env -> mult 2.0
    onprem_res = z_engine.evaluate_component({"primitive": "RSA", "execution_environment": "ON_PREM"})
    assert onprem_res["env_multiplier"] == 2.0
    assert onprem_res["z_score"] == 10.0  # 5 * 2 * 1

    # Hardware env -> mult 3.0
    hsm_res = z_engine.evaluate_component({"primitive": "RSA", "execution_environment": "HARDWARE"})
    assert hsm_res["env_multiplier"] == 3.0
    assert hsm_res["z_score"] == 15.0  # 5 * 3 * 1

    # Embedded env -> mult 4.0
    embed_res = z_engine.evaluate_component({"primitive": "RSA", "execution_environment": "EMBEDDED"})
    assert embed_res["env_multiplier"] == 4.0
    assert embed_res["z_score"] == 20.0  # 5 * 4 * 1


def test_9_different_crypto_ref_array_counts():
    z_engine = ZEngine()

    # 0 refs -> dep_factor 1.0
    ref0_res = z_engine.evaluate_component({"primitive": "RSA", "cryptoRefArray": []})
    assert ref0_res["dep_factor"] == 1.0
    assert ref0_res["z_score"] == 5.0

    # 3 refs -> dep_factor 1.3 (1 + 0.1 * 3)
    ref3_res = z_engine.evaluate_component({"primitive": "RSA", "cryptoRefArray": ["r1", "r2", "r3"]})
    assert ref3_res["dep_factor"] == 1.3
    assert ref3_res["z_score"] == 6.5


def test_10_mosca_uses_z_planning_horizon_years():
    mosca = MoscaEngine()

    # X = 20, Y = 10, RSA Z_score = 5.0 (mapped horizon = 15y, z_val = 10.0)
    comp = {"primitive": "RSA", "algorithm_name": "RSA-2048"}
    res = mosca.evaluate_component_mosca(component=comp, user_x_years=20, user_y_scenario="STANDARD")

    assert res["x"]["value"] == 20
    assert res["y"]["value"] == 10
    assert res["z"]["z_planning_horizon_years"] == 15
    assert res["z"]["z_score"] == 5.0
    assert res["mosca_score"] == 20.0  # 20 + 10 - 10 = 20


def test_11_crypto_asset_response_no_manufactured_defaults(db_session):
    # Verify CryptoAssetResponse schema fields default to None when uncalculated
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
    assert resp.lifetime_label is None
    assert resp.business_criticality_score is None
    assert resp.business_criticality_label is None
