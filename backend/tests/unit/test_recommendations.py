import pytest
from app.recommend.engine import RecommendationEngine
from app.models.enums import CryptoPurpose, QuantumSafety, RecommendationCategory


def test_recommendation_ml_kem():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="ECDH-secp256r1",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        risk_level="HIGH",
        risk_score=70.0
    )

    assert rec["recommended_algorithm"] == "ML-KEM (FIPS 203)"
    assert rec["category"] == RecommendationCategory.PQC_REPLACEMENT
    assert "latency_impact" in rec
    assert "cost_impact" in rec
    assert rec["latency_level"] in ["LOW", "MODERATE"]
    assert rec["cost_level"] in ["LOW", "MODERATE"]
    assert "Latency Impact:" in rec["performance_notes"]
    assert "Cost Impact:" in rec["migration_notes"]


def test_recommendation_ml_dsa():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        risk_level="CRITICAL",
        risk_score=85.0
    )

    assert rec["recommended_algorithm"] == "ML-DSA (FIPS 204)"
    assert rec["category"] == RecommendationCategory.PQC_REPLACEMENT
    assert rec["priority"] == "CRITICAL"
    assert "3.3KB" in rec["latency_impact"] or "Signature size" in rec["latency_impact"]
    assert "certificate chain" in rec["cost_impact"].lower() or "cost" in rec["cost_impact"].lower()


def test_recommendation_aes_retention():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="AES-256-GCM",
        purpose=CryptoPurpose.ENCRYPTION,
        quantum_safety=QuantumSafety.QUANTUM_SAFE,
        risk_level="LOW",
        risk_score=10.0
    )

    assert rec["category"] == RecommendationCategory.RETAIN_SYMMETRIC_CRYPTO
    assert rec["recommended_algorithm"] == "RETAIN_EXISTING"
    assert rec["latency_level"] == "LOW"
    assert rec["cost_level"] == "LOW"
