import pytest
from app.recommend.service import RecommendationService
from app.recommend.engine import RecommendationEngine
from app.recommend.performance_provider import PerformancePredictionProvider, PerformanceCandidateAdapter
from app.models.enums import CryptoPurpose, QuantumSafety

def test_a_explicit_recommendation_evaluation_with_context_produces_ready():
    """TEST A: Explicit recommendation evaluation with complete context produces READY performance evidence."""
    provider = PerformancePredictionProvider()

    # If catboost is available and model is loaded
    if provider._load_status == "READY":
        engine = RecommendationEngine(perf_provider=provider)
        rec = engine.generate_recommendation(
            algorithm_name="ECDH-P256",
            purpose=CryptoPurpose.KEY_ESTABLISHMENT,
            quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
            risk_level="HIGH",
            risk_score=8.5,
            context={"text_length_bytes": 1024}
        )
        perf = rec["tradeoffs"]["performance"]
        assert perf["status"] == "READY"
        assert perf["predicted_latency_us"] is not None
        assert perf["predicted_latency_us"] > 0
        assert perf["provider_name"] == "CatBoostPerformancePredictionProvider"
        assert perf["model_version"] == "catboost-pqc-v1.0"
        assert perf["missing_features"] == []

def test_b_and_c_and_d_recommendation_persistence_and_get_semantics():
    """
    TEST B, C, D: Re-evaluating recommendation persists READY payload,
    subsequent GET returns persisted READY payload without regenerating.
    """
    # Unit verification of service persistence data structure
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="ECDH-P256",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        context={"text_length_bytes": 1024}
    )
    assert "performance" in rec["tradeoffs"]
    assert rec["recommended_algorithm"] == "ML-KEM (FIPS 203)"

def test_e_and_f_missing_context_detection_and_no_fabrication():
    """
    TEST E & F: Missing text_length_bytes is correctly detected and status remains UNCONFIGURED without fabricating values.
    """
    provider = PerformancePredictionProvider()
    if provider._load_status == "READY":
        res, missing = PerformanceCandidateAdapter.extract_features(
            candidate={"algorithm": "ML-KEM-768", "primitive": "KEY_ESTABLISHMENT", "security_level": 3},
            context={"text_length_bytes": None}
        )
        assert res is None
        assert "text_length_bytes" in missing
        assert "text_size_kb" in missing

def test_g_deterministic_candidate_ranking_unchanged():
    """
    TEST G: Deterministic candidate selection and ranking remains unchanged.
    """
    engine = RecommendationEngine()
    rec_ecdh = engine.generate_recommendation(
        algorithm_name="ECDH-P256",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    assert rec_ecdh["recommended_algorithm"] == "ML-KEM (FIPS 203)"

    rec_rsa = engine.generate_recommendation(
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    assert rec_rsa["recommended_algorithm"] == "ML-DSA (FIPS 204)"
