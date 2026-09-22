import pytest
from app.qars.algorithm import (
    extract_parameterized_algorithm_details,
    resolve_algorithm_profile,
    evaluate_algorithm_risk,
)
from app.qars.models import QARSAlgorithmRisk


def test_rsa2048_canonicalization():
    canonical, key_size = extract_parameterized_algorithm_details("RSA-2048")
    assert canonical == "RSA"
    assert key_size == 2048


def test_ecdsa_p256_canonicalization():
    canonical, key_size = extract_parameterized_algorithm_details("ECDSA-P256")
    assert canonical == "ECDSA"
    assert key_size == 256


def test_ecdh_p384_canonicalization():
    canonical, key_size = extract_parameterized_algorithm_details("ECDH-P384")
    assert canonical == "ECDH"
    assert key_size == 384

    canonical_x, key_size_x = extract_parameterized_algorithm_details("X25519")
    assert canonical_x == "ECDH"
    assert key_size_x == 256


def test_aes256_canonicalization():
    canonical, key_size = extract_parameterized_algorithm_details("AES-256")
    assert canonical == "AES"
    assert key_size == 256


def test_sha256_canonicalization():
    canonical, key_size = extract_parameterized_algorithm_details("SHA-256")
    assert canonical == "SHA-256"
    assert key_size is None  # Does not treat 256 as an asymmetric key size


def test_unknown_algorithm():
    res = evaluate_algorithm_risk("SuperQuantumCipher-9000")
    assert res.calibration_status == "UNCONFIGURED"
    assert res.confidence == "INSUFFICIENT_EVIDENCE"
    assert res.aqr_score is None


def test_unconfigured_algorithm_returns_none_aqr():
    res = evaluate_algorithm_risk("UnknownAlgo999")
    assert res.aqr_score is None
    assert res.calibration_status == "UNCONFIGURED"
    assert res.vulnerability_factor is None
    assert res.security_strength_factor is None


def test_configured_algorithm_aqr_calculation():
    calibration_fixture = {
        "RSA": {"vulnerability_factor": 0.9, "security_strength_factor": 0.8}
    }
    res = evaluate_algorithm_risk("RSA-2048", calibration_data=calibration_fixture)
    assert res.calibration_status == "CONFIGURED"
    assert res.vulnerability_factor == 0.9
    assert res.security_strength_factor == 0.8
    assert res.aqr_score == pytest.approx(0.72)


def test_aqr_clamping():
    overflow_fixture = {
        "RSA": {"vulnerability_factor": 1.5, "security_strength_factor": 1.2}
    }
    res_over = evaluate_algorithm_risk("RSA-2048", calibration_data=overflow_fixture)
    assert res_over.aqr_score == 1.0

    underflow_fixture = {
        "RSA": {"vulnerability_factor": -0.5, "security_strength_factor": 0.8}
    }
    res_under = evaluate_algorithm_risk("RSA-2048", calibration_data=underflow_fixture)
    assert res_under.aqr_score == 0.0


def test_shor_attack_family():
    prof_rsa = resolve_algorithm_profile("RSA-2048")
    assert prof_rsa.attack_family == "SHOR"

    prof_ecdsa = resolve_algorithm_profile("ECDSA-P256")
    assert prof_ecdsa.attack_family == "SHOR"


def test_grover_attack_family():
    prof_aes = resolve_algorithm_profile("AES-256")
    assert prof_aes.attack_family == "GROVER"

    prof_sha = resolve_algorithm_profile("SHA-256")
    assert prof_sha.attack_family in ["GROVER", "BHT"]


def test_quantum_attack_naming():
    res_rsa = evaluate_algorithm_risk("RSA-2048")
    assert "Shor" in res_rsa.quantum_attack

    res_aes = evaluate_algorithm_risk("AES-256")
    assert "Grover" in res_aes.quantum_attack


def test_extract_parameterized_details_empty():
    canonical, key_size = extract_parameterized_algorithm_details("", explicit_key_size=1024)
    assert canonical == "UNKNOWN"
    assert key_size == 1024


def test_evaluate_algorithm_risk_empty():
    res = evaluate_algorithm_risk("")
    assert isinstance(res, QARSAlgorithmRisk)
    assert res.canonical_algorithm == "UNKNOWN"
    assert res.aqr_score is None
    assert res.calibration_status == "UNCONFIGURED"


def test_confidence_mapping():
    prof_rsa = resolve_algorithm_profile("RSA-2048")
    assert prof_rsa.confidence in ["PROVISIONAL", "HIGH", "MEDIUM", "LOW", "INSUFFICIENT_EVIDENCE"]
