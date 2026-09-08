import pytest
from app.engines.mosca_engine import MoscaEngine


def test_mosca_numeric_critical():
    engine = MoscaEngine()

    component = {
        "id": "comp-rsa-1",
        "primitive": "RSA",
        "algorithm_name": "RSA-2048",
        "key_size": 2048,
        "location": "src/crypto/auth.py"
    }

    # X = 15 (Banking), Y = 10 (Standard), Z_i = 10 (RSA Shor horizon)
    res = engine.evaluate_component_mosca(
        component=component,
        user_x_years=15,
        user_y_scenario="STANDARD",
        quantum_horizon=10
    )

    assert res["mosca_score"] == 15.0  # 15 + 10 - 10 = 15
    assert res["urgency"] == "CRITICAL"
    assert res["technical_urgency"] == "CRITICAL"
    assert "M_i = X (15y) + Y (10y) - Z_i (10y) = +15 years" in res["explanation"]


def test_mosca_numeric_medium():
    engine = MoscaEngine()

    component = {
        "id": "comp-rsa-2",
        "primitive": "RSA",
        "algorithm_name": "RSA-2048",
        "key_size": 2048,
        "location": "src/temp/helper.py"
    }

    # X = 2, Y = 5 (Fast), Z_i = 10
    res = engine.evaluate_component_mosca(
        component=component,
        user_x_years=2,
        user_y_scenario="FAST",
        quantum_horizon=10
    )

    assert res["mosca_score"] == -3.0  # 2 + 5 - 10 = -3
    assert res["urgency"] == "MEDIUM"
    assert "near boundary" in res["explanation"]


def test_mosca_non_numeric_z():
    engine = MoscaEngine()

    component = {
        "id": "comp-aes-256",
        "primitive": "AES",
        "algorithm_name": "AES-256-GCM",
        "key_size": 256,
        "location": "src/storage/db.py"
    }

    res = engine.evaluate_component_mosca(
        component=component,
        user_x_years=10,
        user_y_scenario="STANDARD"
    )

    assert res["mosca_score"] is None
    assert res["urgency"] == "LOW"
    assert "non-numeric" in res["explanation"]


def test_folder_level_x_override():
    engine = MoscaEngine()

    component = {
        "id": "comp-payments-key",
        "primitive": "RSA",
        "algorithm_name": "RSA-2048",
        "location": "services/payments/vault.py"
    }

    folder_contexts = {
        "services/payments": {"user_x_years": 30, "notes": "PCI-DSS 30y requirement"}
    }

    res = engine.evaluate_component_mosca(
        component=component,
        user_x_years=10,  # Repo-wide default is 10, but payments folder has 30
        user_y_scenario="STANDARD",
        quantum_horizon=10,
        folder_contexts=folder_contexts
    )

    assert res["x"]["value"] == 30
    assert res["mosca_score"] == 30.0  # 30 + 10 - 10 = 30
    assert res["urgency"] == "CRITICAL"


def test_dual_priority_signals():
    engine = MoscaEngine()

    component = {
        "id": "comp-root-cert",
        "primitive": "RSA",
        "algorithm_name": "RSA-4096",
        "criticality": "CRITICAL",
        "location": "pki/root.pem"
    }

    res = engine.evaluate_component_mosca(
        component=component,
        user_x_years=20,
        user_y_scenario="COMPLEX",
        quantum_horizon=10
    )

    assert res["technical_urgency"] == "CRITICAL"
    assert res["business_priority"] == "CRITICAL"


def test_project_mosca_evaluation():
    engine = MoscaEngine()

    class MockProject:
        id = "proj-123"
        name = "FinTech Core"
        user_x_years = 15
        user_domain = "banking"
        user_y_scenario = "STANDARD"

    assets = [
        {"id": "a1", "algorithm_name": "RSA-2048", "location": "src/auth.py"},
        {"id": "a2", "algorithm_name": "AES-256-GCM", "location": "src/crypto.py"},
        {"id": "a3", "algorithm_name": "ML-KEM-768", "location": "src/pqc.py"},
        {"id": "a4", "algorithm_name": "3DES", "location": "legacy/old_enc.py"}
    ]

    proj_res = engine.evaluate_project_mosca(MockProject(), assets)

    assert proj_res["total_components"] == 4
    assert proj_res["critical_components"] == 2  # RSA-2048 & 3DES
    assert proj_res["urgency_distribution"]["CRITICAL"] == 2
