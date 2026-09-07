from app.models.enums import QuantumSafety, CryptoPurpose, RiskLevel, ThreatScenarioType
from app.risk.rules import (
    classify_algorithm_vulnerability,
    determine_crypto_purpose,
    get_sensitivity_score,
    get_criticality_score,
    get_migration_complexity_score,
    get_lifetime_exposure_score
)
from app.risk.mosca import calculate_mosca_analysis
from app.risk.scoring import (
    calculate_deterministic_risk_score,
    get_risk_level_from_score,
    calculate_confidence_score
)
from app.risk.scenarios import evaluate_threat_scenarios
from app.risk.risk_engine import RiskEngine


def test_1_rsa_classification():
    qs, score, rationale = classify_algorithm_vulnerability("RSA-2048")
    assert qs == QuantumSafety.QUANTUM_VULNERABLE
    assert score == 100.0
    assert "Shor's algorithm" in rationale


def test_2_ecdh_classification_and_threat():
    qs, score, _ = classify_algorithm_vulnerability("ECDH")
    purpose = determine_crypto_purpose("ECDH")
    assert qs == QuantumSafety.QUANTUM_VULNERABLE
    assert purpose == CryptoPurpose.KEY_ESTABLISHMENT

    scenarios = evaluate_threat_scenarios(
        algorithm_name="ECDH",
        quantum_safety=qs,
        purpose=purpose,
        data_sensitivity_label="CONFIDENTIAL",
        data_lifetime_years=10.0,
        mosca_status="MIGRATION_REQUIRED"
    )
    stypes = [s["scenario_type"] for s in scenarios]
    assert ThreatScenarioType.HARVEST_NOW_DECRYPT_LATER in stypes


def test_3_ecdsa_classification_and_threat():
    qs, score, _ = classify_algorithm_vulnerability("ECDSA")
    purpose = determine_crypto_purpose("ECDSA")
    assert qs == QuantumSafety.QUANTUM_VULNERABLE
    assert purpose in [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE]

    scenarios = evaluate_threat_scenarios(
        algorithm_name="ECDSA",
        quantum_safety=qs,
        purpose=purpose,
        data_sensitivity_label="CONFIDENTIAL",
        data_lifetime_years=5.0,
        mosca_status="SAFE_MARGIN"
    )
    stypes = [s["scenario_type"] for s in scenarios]
    assert ThreatScenarioType.QUANTUM_SIGNATURE_FORGERY in stypes


def test_4_aes256_classification():
    qs, score, rationale = classify_algorithm_vulnerability("AES-256")
    assert qs == QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN
    assert score == 30.0
    assert "Grover's algorithm" in rationale


def test_5_sha256_classification():
    qs, score, _ = classify_algorithm_vulnerability("SHA-256")
    purpose = determine_crypto_purpose("SHA-256")
    assert qs == QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN
    assert purpose == CryptoPurpose.HASHING
    assert score == 30.0


def test_6_unknown_algorithm():
    qs, score, rationale = classify_algorithm_vulnerability("CUSTOM_CIPHER_99")
    assert qs == QuantumSafety.UNKNOWN
    assert score == 50.0
    assert "could not be definitively classified" in rationale


def test_7_risk_level_thresholds():
    assert get_risk_level_from_score(24.0) == RiskLevel.LOW
    assert get_risk_level_from_score(25.0) == RiskLevel.MODERATE
    assert get_risk_level_from_score(49.0) == RiskLevel.MODERATE
    assert get_risk_level_from_score(50.0) == RiskLevel.HIGH
    assert get_risk_level_from_score(74.0) == RiskLevel.HIGH
    assert get_risk_level_from_score(75.0) == RiskLevel.CRITICAL
    assert get_risk_level_from_score(100.0) == RiskLevel.CRITICAL


def test_8_mosca_safe_margin():
    res = calculate_mosca_analysis(
        data_lifetime_years=2.0,
        migration_time_years=1.0,
        quantum_threat_horizon_year=2040,
        current_year=2026
    )
    assert res["mosca_status"] == "SAFE_MARGIN"
    assert res["mosca_score"] == 20.0


def test_9_mosca_migration_required_and_deadline_risk():
    res = calculate_mosca_analysis(
        data_lifetime_years=10.0,
        migration_time_years=5.0,
        quantum_threat_horizon_year=2033,
        current_year=2026
    )
    # 10 + 5 = 15y protection vs 7y remaining -> gap of 8y
    assert res["mosca_status"] == "DEADLINE_RISK"
    assert res["mosca_score"] == 100.0


def test_10_confidence_independence():
    # Container detector gives 0.55 confidence
    conf = calculate_confidence_score(["ContainerScanner"])
    assert conf == 0.55

    # Evaluate asset with RiskEngine
    engine = RiskEngine()
    eval_res = engine.evaluate_asset_risk(
        algorithm_name="RSA-2048",
        asset_type="CONTAINER",
        detector_names=["ContainerScanner"],
        data_sensitivity_label="CRITICAL"
    )

    # Risk score remains CRITICAL despite confidence being 0.55
    assert eval_res["risk_score"] >= 75.0
    assert eval_res["risk_level"] == "CRITICAL"
    assert eval_res["confidence_score"] == 0.55


def test_11_hndl_scenario():
    scenarios = evaluate_threat_scenarios(
        algorithm_name="RSA-2048",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        data_sensitivity_label="RESTRICTED",
        data_lifetime_years=10.0,
        mosca_status="MIGRATION_REQUIRED"
    )
    stypes = [s["scenario_type"] for s in scenarios]
    assert ThreatScenarioType.HARVEST_NOW_DECRYPT_LATER in stypes


def test_12_signature_forgery_scenario():
    scenarios = evaluate_threat_scenarios(
        algorithm_name="Ed25519",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        data_sensitivity_label="CONFIDENTIAL",
        data_lifetime_years=3.0,
        mosca_status="SAFE_MARGIN"
    )
    stypes = [s["scenario_type"] for s in scenarios]
    assert ThreatScenarioType.QUANTUM_SIGNATURE_FORGERY in stypes


def test_13_deterministic_risk_scoring_formula():
    score = calculate_deterministic_risk_score(
        quantum_exposure=100.0,
        data_sensitivity=80.0,
        business_criticality=75.0,
        migration_complexity=50.0,
        lifetime_exposure=80.0
    )
    assert score == 80.8
    assert get_risk_level_from_score(score) == RiskLevel.CRITICAL


if __name__ == "__main__":
    test_1_rsa_classification()
    test_2_ecdh_classification_and_threat()
    test_3_ecdsa_classification_and_threat()
    test_4_aes256_classification()
    test_5_sha256_classification()
    test_6_unknown_algorithm()
    test_7_risk_level_thresholds()
    test_8_mosca_safe_margin()
    test_9_mosca_migration_required_and_deadline_risk()
    test_10_confidence_independence()
    test_11_hndl_scenario()
    test_12_signature_forgery_scenario()
    test_13_deterministic_risk_scoring_formula()
    print("ALL PROMPT 3 UNIT TESTS PASSED SUCCESSFULLY!")
