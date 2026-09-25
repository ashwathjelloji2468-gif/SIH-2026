import math
import json
import pytest
from app.models.enums import CryptoPurpose, QuantumSafety, RecommendationCategory
from app.recommend.engine import RecommendationEngine
from app.recommend.performance_provider import (
    PerformancePredictionProvider,
    PerformanceCandidateAdapter,
    FEATURE_COLUMNS,
)


class MockReadyPerformanceProvider(PerformancePredictionProvider):
    """Mock performance provider simulating a loaded CatBoost model."""
    def __init__(self, latencies=None):
        super().__init__(model_path=None)
        self._load_status = "READY"
        self._load_reason = None
        self.provider_name = "MockCatBoostPerformanceProvider"
        self._metadata = {
            "model_version": "catboost-pqc-v1.2",
            "dataset_version": "openssl-bench-2026.3",
            "benchmark_source": "liboqs/OpenSSL benchmark experiments"
        }
        self.latencies = latencies or {"ML-KEM-768": 150.5, "ML-DSA-65": 220.0, "ML-KEM-512": 95.0, "ML-KEM-1024": 310.0}
        self.called_candidates = []

    def predict_performance(self, candidate, context=None):
        cand_name = candidate.get("algorithm") or candidate.get("candidate", "UNKNOWN")
        self.called_candidates.append(cand_name)

        lat = self.latencies.get(cand_name, 180.0)
        return {
            "status": "READY",
            "reason": None,
            "candidate": cand_name,
            "predicted_latency_us": lat,
            "predicted_throughput_ops_s": None,  # Throughput model unavailable
            "model_version": self._metadata["model_version"],
            "dataset_version": self._metadata["dataset_version"],
            "provider_name": self.provider_name,
            "benchmark_source": self._metadata["benchmark_source"],
            "evidence": [f"Mock CatBoost predicted CPU latency: {lat} µs."],
            "warnings": [],
            "missing_features": []
        }


def test_a_output_contract():
    provider = PerformancePredictionProvider(model_path=None)
    res = provider.predict_performance({"algorithm": "ML-KEM-768", "primitive": "KEY_ESTABLISHMENT", "security_level": 3})
    assert "status" in res
    assert "reason" in res
    assert "candidate" in res
    assert "predicted_latency_us" in res
    assert "predicted_throughput_ops_s" in res
    assert "model_version" in res
    assert "dataset_version" in res
    assert "provider_name" in res
    assert "benchmark_source" in res
    assert "evidence" in res
    assert "warnings" in res
    assert "missing_features" in res
    assert res["predicted_throughput_ops_s"] is None
    assert res["reason"] == "MODEL_ARTIFACT_NOT_CONFIGURED"
    assert res["warnings"] == ["MODEL_ARTIFACT_NOT_CONFIGURED"]


def test_b_missing_artifact_unconfigured():
    provider = PerformancePredictionProvider(model_path=None)
    assert provider._load_status == "UNCONFIGURED"
    res = provider.predict_performance({"algorithm": "ML-KEM-768"})
    assert res["status"] == "UNCONFIGURED"
    assert res["reason"] == "MODEL_ARTIFACT_NOT_CONFIGURED"
    assert res["predicted_latency_us"] is None


def test_c_invalid_artifact_error(tmp_path):
    invalid_file = tmp_path / "invalid_model.cbm"
    invalid_file.write_text("invalid content")

    provider = PerformancePredictionProvider(model_path=str(invalid_file))
    assert provider._load_status == "ERROR"
    res = provider.predict_performance({"algorithm": "ML-KEM-768"})
    assert res["status"] == "ERROR"


def test_d_mocked_ready_provider():
    mock_provider = MockReadyPerformanceProvider({"ML-KEM-768": 142.5})
    res = mock_provider.predict_performance({"algorithm": "ML-KEM-768", "primitive": "KEM", "security_level": 3})
    assert res["status"] == "READY"
    assert res["predicted_latency_us"] == 142.5
    assert res["predicted_throughput_ops_s"] is None


def test_e_rejected_candidate_never_reaches_provider():
    mock_provider = MockReadyPerformanceProvider()
    engine = RecommendationEngine(perf_provider=mock_provider)

    rec = engine.generate_recommendation("ECDSA", CryptoPurpose.DIGITAL_SIGNATURE, QuantumSafety.QUANTUM_VULNERABLE)

    called = mock_provider.called_candidates
    assert not any("ML-KEM" in c for c in called)


def test_f_eligible_candidate_reaches_provider():
    mock_provider = MockReadyPerformanceProvider()
    engine = RecommendationEngine(perf_provider=mock_provider)

    rec = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    called = mock_provider.called_candidates
    assert any("ML-KEM" in c for c in called)


def test_g_missing_feature_unconfigured():
    candidate = {"algorithm": "ML-KEM-768"}
    features, missing = PerformanceCandidateAdapter.extract_features(candidate, context=None)
    assert features is None
    assert "security_level" in missing or "primitive" in missing


def test_exact_10_feature_kem_vector():
    kem_candidate = {
        "algorithm": "ML-KEM-768",
        "primitive": "KEY_ESTABLISHMENT",
        "security_level": 3,
        "ciphertext_size_bytes": 1088,
        "shared_secret_bytes": 32,
    }
    kem_ctx = {"text_length_bytes": 2048}
    kem_feats, missing_kem = PerformanceCandidateAdapter.extract_features(kem_candidate, kem_ctx)

    assert missing_kem == []
    assert list(kem_feats.keys()) == FEATURE_COLUMNS
    assert kem_feats["algorithm"] == "ML-KEM-768"
    assert kem_feats["security_level"] == 3
    assert kem_feats["security_level_bits"] == 192
    assert kem_feats["text_size_kb"] == 2.0
    assert kem_feats["text_length_bytes"] == 2048
    assert kem_feats["primitive"] == "KEM"
    assert kem_feats["ciphertext_length"] == 1088
    assert math.isnan(kem_feats["signature_length"])
    assert kem_feats["overhead_bytes"] == 1088
    assert kem_feats["shared_secret_length"] == 32


def test_exact_10_feature_signature_vector():
    sig_candidate = {
        "algorithm": "ML-DSA-65",
        "primitive": "DIGITAL_SIGNATURE",
        "security_level": 3,
        "signature_size_bytes": 3309,
    }
    sig_ctx = {"text_length_bytes": 1024}
    sig_feats, missing_sig = PerformanceCandidateAdapter.extract_features(sig_candidate, sig_ctx)

    assert missing_sig == []
    assert list(sig_feats.keys()) == FEATURE_COLUMNS
    assert sig_feats["algorithm"] == "ML-DSA-65"
    assert sig_feats["security_level"] == 3
    assert sig_feats["security_level_bits"] == 192
    assert sig_feats["text_size_kb"] == 1.0
    assert sig_feats["text_length_bytes"] == 1024
    assert sig_feats["primitive"] == "SIGNATURE"
    assert math.isnan(sig_feats["ciphertext_length"])
    assert sig_feats["signature_length"] == 3309
    assert sig_feats["overhead_bytes"] == 3309
    assert math.isnan(sig_feats["shared_secret_length"])


def test_nan_handling_for_non_applicable_fields():
    kem_candidate = {
        "algorithm": "ML-KEM-768",
        "primitive": "KEM",
        "security_level": 3,
        "ciphertext_size_bytes": 1088
    }
    kem_feats, _ = PerformanceCandidateAdapter.extract_features(kem_candidate, {"text_length_bytes": 1024})
    assert math.isnan(kem_feats["signature_length"])

    sig_candidate = {
        "algorithm": "ML-DSA-65",
        "primitive": "SIGNATURE",
        "security_level": 3,
        "signature_size_bytes": 3309
    }
    sig_feats, _ = PerformanceCandidateAdapter.extract_features(sig_candidate, {"text_length_bytes": 1024})
    assert math.isnan(sig_feats["ciphertext_length"])
    assert math.isnan(sig_feats["shared_secret_length"])


def test_log1p_model_prediction_and_expm1_transform(tmp_path):
    class MockCatBoostModel:
        def predict(self, df):
            return [math.log1p(150.0)]

    model_file = tmp_path / "pqc_model_log_v1.cbm"
    model_file.write_text("dummy binary")
    meta_file = tmp_path / "pqc_model_log_v1.cbm.json"
    meta_file.write_text(json.dumps({
        "model_version": "catboost-pqc-v1.0",
        "dataset_version": "nist-pqc-bench-v1.0",
        "benchmark_source": "NIST benchmark",
        "training_target": "log1p(latency_us)",
        "prediction_inverse_transform": "expm1"
    }))

    provider = PerformancePredictionProvider(model_path=str(model_file))
    provider._model = MockCatBoostModel()
    provider._load_status = "READY"
    provider._load_reason = None

    cand = {"algorithm": "ML-KEM-768", "primitive": "KEM", "security_level": 3, "ciphertext_size_bytes": 1088}
    res = provider.predict_performance(cand, {"text_length_bytes": 1024})
    assert res["status"] == "READY"
    assert res["predicted_latency_us"] == 150.0


def test_raw_latency_model_backwards_compatibility(tmp_path):
    class MockRawCatBoostModel:
        def predict(self, df):
            return [150.0]

    model_file = tmp_path / "pqc_model_raw.cbm"
    model_file.write_text("dummy binary")
    meta_file = tmp_path / "pqc_model_raw.cbm.json"
    meta_file.write_text(json.dumps({
        "model_version": "catboost-pqc-v0.9",
        "dataset_version": "openssl-bench-2026.1",
        "benchmark_source": "OpenSSL bench",
        "training_target": "latency_us",
        "prediction_inverse_transform": "identity"
    }))

    provider = PerformancePredictionProvider(model_path=str(model_file))
    provider._model = MockRawCatBoostModel()
    provider._load_status = "READY"
    provider._load_reason = None

    cand = {"algorithm": "ML-KEM-768", "primitive": "KEM", "security_level": 3, "ciphertext_size_bytes": 1088}
    res = provider.predict_performance(cand, {"text_length_bytes": 1024})
    assert res["status"] == "READY"
    assert res["predicted_latency_us"] == 150.0


def test_missing_metadata_error(tmp_path):
    model_file = tmp_path / "model_without_meta.cbm"
    model_file.write_text("dummy content")

    provider = PerformancePredictionProvider(model_path=str(model_file))
    assert provider._load_status == "ERROR"
    assert "Companion metadata JSON file missing" in provider._load_reason


def test_real_bundled_artifact_integration():
    import os
    bundled_path = "app/recommend/models/pqc_model_log_v1.cbm"
    resolved_path = PerformancePredictionProvider()._resolve_path(bundled_path)
    if not resolved_path or not os.path.exists(resolved_path):
        pytest.skip("Real bundled model artifact not present in local test environment")

    provider = PerformancePredictionProvider(model_path=bundled_path)
    assert provider._load_status == "READY"
    assert provider._metadata is not None
    assert provider._metadata.get("training_target") == "log1p(latency_us)"
    assert provider._metadata.get("prediction_inverse_transform") == "expm1"

    cand = {
        "algorithm": "ML-KEM-768",
        "primitive": "KEY_ESTABLISHMENT",
        "security_level": 3,
        "ciphertext_size_bytes": 1088,
        "shared_secret_bytes": 32,
    }
    res = provider.predict_performance(cand, {"text_length_bytes": 2048})
    assert res["status"] == "READY"
    assert res["predicted_latency_us"] is not None
    assert isinstance(res["predicted_latency_us"], float)
    assert res["predicted_latency_us"] > 0
    assert res["predicted_throughput_ops_s"] is None


def test_h_no_fabricated_prediction():
    provider = PerformancePredictionProvider(model_path=None)
    res = provider.predict_performance({"algorithm": "ML-KEM-768"})
    assert res["predicted_latency_us"] is None
    assert res["predicted_throughput_ops_s"] is None


def test_i_deterministic_output_when_provider_unavailable():
    unconfig_provider = PerformancePredictionProvider(model_path=None)
    engine = RecommendationEngine(perf_provider=unconfig_provider)
    rec = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    assert rec["category"] == RecommendationCategory.PQC_REPLACEMENT
    assert rec["performance"]["status"] == "UNCONFIGURED"


def test_j_hard_latency_constraint_only_with_ready_prediction():
    unconfig_provider = PerformancePredictionProvider(model_path=None)
    engine1 = RecommendationEngine(perf_provider=unconfig_provider)
    rec1 = engine1.generate_recommendation(
        "ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE,
        max_latency_us=50.0
    )
    assert len(rec1["eligible_candidates"]) > 0

    mock_slow = MockReadyPerformanceProvider({"ML-KEM-1024": 310.0, "ML-KEM-768": 200.0, "ML-KEM-512": 150.0})
    engine2 = RecommendationEngine(perf_provider=mock_slow)
    rec2 = engine2.generate_recommendation(
        "ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE,
        max_latency_us=180.0
    )
    rejected_names = [c["candidate"] for c in rec2["rejected_candidates"]]
    assert "ML-KEM-1024" in rejected_names or "ML-KEM-768" in rejected_names


def test_k_performance_evidence_persists_and_returns():
    mock_provider = MockReadyPerformanceProvider({"ML-KEM-768": 135.0})
    engine = RecommendationEngine(perf_provider=mock_provider)
    rec = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    assert "performance" in rec
    assert rec["performance"]["predicted_latency_us"] == 135.0
    assert rec["tradeoffs"]["performance"]["predicted_latency_us"] == 135.0


def test_l_persistence_semantics_unchanged():
    from app.recommend.service import RecommendationService
    svc = RecommendationService(db=None)
    assert hasattr(svc, "recommend_asset")


def test_m_get_does_not_regenerate():
    from app.recommend.service import RecommendationService
    class DummyRepo:
        def get_latest_for_asset(self, asset_id):
            return type("Rec", (), {"id": "rec_123", "asset_id": asset_id, "target_pqc_candidate": "STORED_ML_KEM", "recommended_algorithm": "STORED_ML_KEM", "alternative_algorithm": None, "category": RecommendationCategory.PQC_REPLACEMENT, "priority": "HIGH", "standard_status": "FINAL_STANDARD", "rationale": "Stored rationale", "compatibility_notes": None, "performance_notes": None, "tradeoffs": {"performance": {"status": "READY", "predicted_latency_us": 120.0}}, "threat_scenarios": [], "migration_notes": "", "migration_complexity": "MEDIUM", "confidence": 0.9, "kb_version": "2026.3.0", "risk_assessment_id": None, "created_at": "2026-09-23T12:00:00"})()

    class DummyAssetRepo:
        def get(self, asset_id):
            return type("Asset", (), {"id": asset_id, "name": "Asset1", "algorithm_name": "ECDH", "purpose": CryptoPurpose.KEY_ESTABLISHMENT, "quantum_safety": QuantumSafety.QUANTUM_VULNERABLE, "scan": None, "location": "app.py", "line_number": 10})()

    svc = RecommendationService(db=None)
    svc.asset_repo = DummyAssetRepo()
    svc.rec_repo = DummyRepo()

    res = svc.recommend_asset("asset_123", force_regeneration=False)
    assert res["target_pqc_candidate"] == "STORED_ML_KEM"
    assert res["tradeoffs"]["performance"]["predicted_latency_us"] == 120.0


def test_n_explicit_evaluation_regenerates():
    from app.recommend.service import RecommendationService
    class DummyAssetRepo:
        def get(self, asset_id):
            return type("Asset", (), {"id": asset_id, "name": "Asset1", "algorithm_name": "ECDH", "purpose": CryptoPurpose.KEY_ESTABLISHMENT, "quantum_safety": QuantumSafety.QUANTUM_VULNERABLE, "scan": None, "location": "app.py", "line_number": 10, "evidence_items": []})()

    svc = RecommendationService(db=None)
    svc.asset_repo = DummyAssetRepo()
    svc.rec_repo = None

    res = svc.recommend_asset("asset_123", force_regeneration=True)
    assert "ML-KEM" in res["target_pqc_candidate"]


def test_o_scan_enrichment_regenerates():
    mock_provider = MockReadyPerformanceProvider({"ML-KEM-768": 110.0})
    engine = RecommendationEngine(perf_provider=mock_provider)
    rec = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    assert rec["performance"]["status"] == "READY"
