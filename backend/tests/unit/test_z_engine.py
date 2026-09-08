import pytest
from app.engines.z_engine import (
    ZEngine, DEFAULT_QUANTUM_HORIZON, CURRENT_YEAR,
    QUANTUM_CLASS_SHOR, QUANTUM_CLASS_STRENGTH_REDUCTION,
    QUANTUM_CLASS_PQC, QUANTUM_CLASS_HYBRID, QUANTUM_CLASS_UNKNOWN,
    STATUS_VULNERABLE_AT_HORIZON, STATUS_UNACCEPTABLE_AT_HORIZON,
    STATUS_REDUCED_BUT_ACCEPTABLE, STATUS_REQUIRES_REVIEW, STATUS_NO_IMMEDIATE_DEADLINE
)

def test_rsa_ecc_shor_vulnerable():
    engine = ZEngine(default_horizon=10)

    # RSA-2048
    rsa_res = engine.evaluate_component({
        "id": "asset-rsa-1",
        "primitive": "RSA",
        "algorithm_name": "RSA-2048",
        "key_size": 2048
    })
    assert rsa_res["quantum_class"] == QUANTUM_CLASS_SHOR
    assert rsa_res["status"] == STATUS_VULNERABLE_AT_HORIZON
    assert rsa_res["z_value"] == 10.0
    assert rsa_res["quantum_security_bits"] == 0
    assert "Shor's algorithm" in rsa_res["explanation"]

    # ECDSA-P256
    ecdsa_res = engine.evaluate_component({
        "id": "asset-ecdsa-1",
        "primitive": "ECDSA",
        "algorithm_name": "ECDSA-P256",
        "key_size": 256
    })
    assert ecdsa_res["quantum_class"] == QUANTUM_CLASS_SHOR
    assert ecdsa_res["status"] == STATUS_VULNERABLE_AT_HORIZON
    assert ecdsa_res["z_value"] == 10.0
    assert ecdsa_res["quantum_security_bits"] == 0


def test_aes_grover_reduction():
    engine = ZEngine(default_horizon=10)

    # AES-128 -> Requires review (halved to ~64 bits)
    aes128_res = engine.evaluate_component({
        "id": "asset-aes-128",
        "primitive": "AES",
        "algorithm_name": "AES-128-GCM",
        "key_size": 128
    })
    assert aes128_res["quantum_class"] == QUANTUM_CLASS_STRENGTH_REDUCTION
    assert aes128_res["status"] == STATUS_REQUIRES_REVIEW
    assert aes128_res["z_value"] is None
    assert aes128_res["quantum_security_bits"] == 64
    assert "Grover's search algorithm" in aes128_res["explanation"]

    # AES-256 -> Reduced but acceptable (~128 bits)
    aes256_res = engine.evaluate_component({
        "id": "asset-aes-256",
        "primitive": "AES",
        "algorithm_name": "AES-256-CBC",
        "key_size": 256
    })
    assert aes256_res["quantum_class"] == QUANTUM_CLASS_STRENGTH_REDUCTION
    assert aes256_res["status"] == STATUS_REDUCED_BUT_ACCEPTABLE
    assert aes256_res["z_value"] is None
    assert aes256_res["quantum_security_bits"] == 128


def test_legacy_primitives_unacceptable():
    engine = ZEngine(default_horizon=10)

    des_res = engine.evaluate_component({
        "id": "asset-3des",
        "primitive": "3DES",
        "algorithm_name": "DES-EDE3-CBC"
    })
    assert des_res["quantum_class"] == QUANTUM_CLASS_STRENGTH_REDUCTION
    assert des_res["status"] == STATUS_UNACCEPTABLE_AT_HORIZON
    assert des_res["z_value"] == 10.0
    assert des_res["quantum_security_bits"] in (32, 40)


def test_pqc_resistant_no_deadline():
    engine = ZEngine(default_horizon=10)

    ml_kem_res = engine.evaluate_component({
        "id": "asset-ml-kem",
        "primitive": "ML-KEM",
        "algorithm_name": "ML-KEM-768"
    })
    assert ml_kem_res["quantum_class"] == QUANTUM_CLASS_PQC
    assert ml_kem_res["status"] == STATUS_NO_IMMEDIATE_DEADLINE
    assert ml_kem_res["z_value"] is None
    assert "Post-quantum cryptographic primitive" in ml_kem_res["explanation"]


def test_hybrid_composite():
    engine = ZEngine(default_horizon=10)

    hybrid_res = engine.evaluate_component({
        "id": "asset-hybrid",
        "primitive": "HYBRID",
        "algorithm_name": "RSA-2048+ML-KEM-768"
    })
    assert hybrid_res["quantum_class"] == QUANTUM_CLASS_HYBRID
    assert hybrid_res["status"] == STATUS_REDUCED_BUT_ACCEPTABLE
    assert hybrid_res["z_value"] is None


def test_unknown_primitive():
    engine = ZEngine(default_horizon=10)

    unknown_res = engine.evaluate_component({
        "id": "asset-unknown",
        "primitive": "CUSTOM_PROPRIETARY",
        "algorithm_name": "CUSTOM_PROPRIETARY"
    })
    assert unknown_res["quantum_class"] == QUANTUM_CLASS_UNKNOWN
    assert unknown_res["status"] == STATUS_REQUIRES_REVIEW
    assert unknown_res["confidence"] == "LOW"


def test_project_evaluation():
    engine = ZEngine(default_horizon=10)
    assets = [
        {"id": "1", "algorithm_name": "RSA-2048", "key_size": 2048},
        {"id": "2", "algorithm_name": "AES-256-GCM", "key_size": 256},
        {"id": "3", "algorithm_name": "ML-KEM-768"},
        {"id": "4", "algorithm_name": "3DES"}
    ]
    proj_eval = engine.evaluate_project(assets, quantum_horizon=10)
    assert proj_eval["total_components"] == 4
    assert proj_eval["vulnerable_components"] == 2  # RSA-2048 and 3DES
    assert proj_eval["class_breakdown"][QUANTUM_CLASS_SHOR] == 1
    assert proj_eval["class_breakdown"][QUANTUM_CLASS_STRENGTH_REDUCTION] == 2
    assert proj_eval["class_breakdown"][QUANTUM_CLASS_PQC] == 1
