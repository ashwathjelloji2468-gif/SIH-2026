from app.models.enums import CryptoPurpose, QuantumSafety, RecommendationCategory
from app.recommend.engine import RecommendationEngine

def test_1_rsa_digital_signature():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    assert rec["recommended_algorithm"] == "ML-DSA (FIPS 204)"
    assert rec["category"] == RecommendationCategory.PQC_REPLACEMENT
    assert "ML-DSA" in rec["rationale"]


def test_2_ecdsa_digital_signature():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="ECDSA",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    assert rec["recommended_algorithm"] == "ML-DSA (FIPS 204)"
    assert rec["alternative_algorithm"] == "SLH-DSA (FIPS 205)"
    assert rec["category"] == RecommendationCategory.PQC_REPLACEMENT


def test_3_ecdh_key_establishment():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="ECDH",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    assert rec["recommended_algorithm"] == "ML-KEM (FIPS 203)"
    assert rec["alternative_algorithm"] == "HYBRID (ECDH + ML-KEM)"
    assert rec["category"] == RecommendationCategory.PQC_REPLACEMENT


def test_4_dh_key_establishment():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="DH",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    assert rec["recommended_algorithm"] == "ML-KEM (FIPS 203)"
    assert rec["category"] == RecommendationCategory.PQC_REPLACEMENT


def test_5_aes256_encryption():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="AES-256",
        purpose=CryptoPurpose.ENCRYPTION,
        quantum_safety=QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN
    )
    assert rec["category"] == RecommendationCategory.RETAIN_SYMMETRIC_CRYPTO
    assert rec["recommended_algorithm"] == "RETAIN_EXISTING"
    assert rec["recommended_algorithm"] != "ML-KEM"
    assert rec["recommended_algorithm"] != "ML-DSA"
    assert "Symmetric encryption algorithm 'AES-256' is not broken by Shor's algorithm" in rec["rationale"]


def test_6_sha256_hashing():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="SHA-256",
        purpose=CryptoPurpose.HASHING,
        quantum_safety=QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN
    )
    assert rec["category"] == RecommendationCategory.RETAIN_HASH
    assert rec["recommended_algorithm"] == "RETAIN_EXISTING"


def test_7_hmac():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="HMAC-SHA256",
        purpose=CryptoPurpose.MAC,
        quantum_safety=QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN
    )
    assert rec["category"] == RecommendationCategory.RETAIN_MAC
    assert rec["recommended_algorithm"] == "RETAIN_EXISTING"


def test_8_pbkdf2():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="PBKDF2",
        purpose=CryptoPurpose.PASSWORD_DERIVATION,
        quantum_safety=QuantumSafety.NOT_DIRECTLY_QUANTUM_VULNERABLE
    )
    assert rec["category"] == RecommendationCategory.RETAIN_PASSWORD_DERIVATION
    assert rec["recommended_algorithm"] == "RETAIN_EXISTING"


def test_9_unknown_algorithm():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="CUSTOM_CIPHER",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.UNKNOWN
    )
    assert rec["recommended_algorithm"] == "ML-KEM (FIPS 203)"


def test_10_unknown_purpose():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="UNKNOWN_ALG",
        purpose=CryptoPurpose.UNKNOWN,
        quantum_safety=QuantumSafety.UNKNOWN
    )
    assert rec["category"] == RecommendationCategory.MANUAL_REVIEW
    assert rec["recommended_algorithm"] == "MANUAL_REVIEW_REQUIRED"


def test_11_hndl_scenario_recommendation():
    engine = RecommendationEngine()
    threats = [{"scenario_type": "HARVEST_NOW_DECRYPT_LATER"}]
    rec = engine.generate_recommendation(
        algorithm_name="ECDH",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        threat_scenarios=threats
    )
    assert rec["recommended_algorithm"] == "ML-KEM (FIPS 203)"
    assert "Harvest-Now, Decrypt-Later" in rec["rationale"]


def test_12_signature_forgery_scenario_recommendation():
    engine = RecommendationEngine()
    threats = [{"scenario_type": "QUANTUM_SIGNATURE_FORGERY"}]
    rec = engine.generate_recommendation(
        algorithm_name="ECDSA",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        threat_scenarios=threats
    )
    assert rec["recommended_algorithm"] == "ML-DSA (FIPS 204)"
    assert "digital signature forgery" in rec["rationale"]


def test_13_critical_risk_urgency():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        risk_level="CRITICAL",
        risk_score=85.0
    )
    assert rec["priority"] == "CRITICAL"


def test_14_low_risk_urgency():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="SHA-256",
        purpose=CryptoPurpose.HASHING,
        quantum_safety=QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN,
        risk_level="LOW",
        risk_score=15.0
    )
    assert rec["priority"] == "LOW"


def test_15_confidence_separation():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        risk_level="CRITICAL",
        risk_score=90.0,
        detector_names=["BinaryScanner"]
    )
    assert rec["priority"] == "CRITICAL"
    assert rec["confidence"] == 0.65


def test_16_determinism():
    engine = RecommendationEngine()
    r1 = engine.generate_recommendation(
        algorithm_name="ECDH",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        risk_level="HIGH",
        risk_score=70.0
    )
    r2 = engine.generate_recommendation(
        algorithm_name="ECDH",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        risk_level="HIGH",
        risk_score=70.0
    )
    assert r1["recommended_algorithm"] == r2["recommended_algorithm"]
    assert r1["category"] == r2["category"]
    assert r1["priority"] == r2["priority"]
    assert r1["confidence"] == r2["confidence"]
    assert r1["rationale"] == r2["rationale"]


if __name__ == "__main__":
    test_1_rsa_digital_signature()
    test_2_ecdsa_digital_signature()
    test_3_ecdh_key_establishment()
    test_4_dh_key_establishment()
    test_5_aes256_encryption()
    test_6_sha256_hashing()
    test_7_hmac()
    test_8_pbkdf2()
    test_9_unknown_algorithm()
    test_10_unknown_purpose()
    test_11_hndl_scenario_recommendation()
    test_12_signature_forgery_scenario_recommendation()
    test_13_critical_risk_urgency()
    test_14_low_risk_urgency()
    test_15_confidence_separation()
    test_16_determinism()
    print("ALL PROMPT 4 UNIT TESTS PASSED SUCCESSFULLY!")
