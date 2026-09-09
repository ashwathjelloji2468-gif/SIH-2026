import pytest
from app.knowledge.crypto_catalog import evaluate_quantum_assessment
from app.normalization.crypto_asset_normalizer import determine_quantum_safety
from app.models.enums import QuantumSafety, CryptoPurpose

def test_quantum_assessment_rsa():
    res = evaluate_quantum_assessment("RSA-2048", key_size=2048, purpose=CryptoPurpose.SIGNATURE)
    assert res["quantum_status"] == "CRITICAL"
    assert res["attack_algorithm"] == "Shor's Algorithm"
    assert res["confidence"] == "HIGH"
    assert "polynomial time" in res["quantum_effect"].lower() or "shor" in res["quantum_effect"].lower()
    assert "ML-KEM" in res["recommended_action"] or "ML-DSA" in res["recommended_action"]

def test_quantum_assessment_ecdsa_ecdh():
    for alg in ["ECDSA-P256", "ECDH-P384", "Ed25519", "X25519"]:
        res = evaluate_quantum_assessment(alg)
        assert res["quantum_status"] == "CRITICAL"
        assert res["attack_algorithm"] == "Shor's Algorithm"
        assert res["confidence"] == "HIGH"

def test_quantum_assessment_aes_parameters():
    # AES-128
    res_128 = evaluate_quantum_assessment("AES-128", key_size=128)
    assert res_128["quantum_status"] == "PARAMETER_DEPENDENT"
    assert res_128["attack_algorithm"] == "Grover's Algorithm"
    assert res_128["confidence"] == "HIGH"

    # AES-256
    res_256 = evaluate_quantum_assessment("AES-256", key_size=256)
    assert res_256["quantum_status"] == "LOW"
    assert res_256["attack_algorithm"] == "Grover's Algorithm"

def test_quantum_assessment_hash_functions():
    # SHA-256
    res_sha256 = evaluate_quantum_assessment("SHA-256")
    assert res_sha256["quantum_status"] == "LOW"
    assert "Grover" in res_sha256["attack_algorithm"]
    assert "BHT" in res_sha256["attack_algorithm"]

    # MD5
    res_md5 = evaluate_quantum_assessment("MD5")
    assert res_md5["quantum_status"] == "CRITICAL"
    assert "Grover" in res_md5["attack_algorithm"]

def test_quantum_assessment_unknown_algorithm():
    res = evaluate_quantum_assessment("UNKNOWN_PROPRIETARY_CIPHER")
    assert res["quantum_status"] == "UNKNOWN"
    assert res["confidence"] == "INSUFFICIENT_EVIDENCE"
    assert res["recommended_action"] == "MANUAL_CRYPTOGRAPHIC_REVIEW"

def test_normalizer_quantum_safety_integration():
    assert determine_quantum_safety("RSA-2048", 2048) == QuantumSafety.QUANTUM_VULNERABLE
    assert determine_quantum_safety("AES-256", 256) == QuantumSafety.QUANTUM_SAFE
    assert determine_quantum_safety("AES-128", 128) == QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN
    assert determine_quantum_safety("SHA-256") == QuantumSafety.QUANTUM_SAFE
    assert determine_quantum_safety("MD5") == QuantumSafety.QUANTUM_VULNERABLE
    assert determine_quantum_safety("FOOBAR_CIPHER_99") == QuantumSafety.UNKNOWN
