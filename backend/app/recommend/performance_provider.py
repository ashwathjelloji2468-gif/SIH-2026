import os
import json
from typing import Dict, Any, List, Optional, Tuple

class PerformanceCandidateAdapter:
    """
    Adapter converting SENTRIQ candidate and application context into
    the exact feature schema required by the PQC performance model.
    """
    @staticmethod
    def extract_features(candidate: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Extract exact feature schema for KEM or Signature models without fabricating missing values.
        Returns (feature_dict, list_of_missing_features).
        """
        cand_name = candidate.get("algorithm") or candidate.get("candidate")
        primitive = (candidate.get("primitive") or "").upper()
        sec_level = candidate.get("security_level")
        ciphertext_size = candidate.get("ciphertext_size_bytes")
        signature_size = candidate.get("signature_size_bytes")
        
        ctx = context or {}
        text_len = ctx.get("text_length_bytes") if ctx.get("text_length_bytes") is not None else (
            ctx.get("payload_size_bytes") if ctx.get("payload_size_bytes") is not None else ctx.get("message_size_bytes")
        )

        missing_features = []
        features = {}

        if not cand_name:
            missing_features.append("algorithm")
        else:
            features["algorithm"] = cand_name

        if sec_level is None:
            missing_features.append("security_level")
        else:
            features["security_level"] = sec_level
            sec_bits_map = {1: 128, 2: 128, 3: 192, 4: 192, 5: 256}
            features["security_level_bits"] = sec_bits_map.get(sec_level, 128)

        if text_len is None:
            missing_features.append("text_length_bytes")
            missing_features.append("text_size_kb")
        else:
            features["text_size_kb"] = round(text_len / 1024.0, 4)
            features["text_length_bytes"] = text_len

        if "KEY_ESTABLISHMENT" in primitive or "KEM" in primitive:
            features["primitive"] = "KEM"
            if ciphertext_size is None:
                missing_features.append("ciphertext_length")
            else:
                features["ciphertext_length"] = ciphertext_size
                features["overhead_bytes"] = ciphertext_size
            features["shared_secret_length"] = 32

        elif "DIGITAL_SIGNATURE" in primitive or "SIGNATURE" in primitive:
            features["primitive"] = "SIGNATURE"
            if signature_size is None:
                missing_features.append("signature_length")
            else:
                features["signature_length"] = signature_size
                features["overhead_bytes"] = signature_size
        else:
            missing_features.append("primitive")

        if missing_features:
            return None, missing_features

        return features, []


class PerformancePredictionProvider:
    """
    Performance Prediction Provider for SENTRIQ Recommendation Engine.
    
    Lazily loads CatBoost model artifacts when SENTRIQ_PERFORMANCE_MODEL_PATH is set.
    When unconfigured, missing, or invalid, returns status = UNCONFIGURED or ERROR
    without fabricating prediction values.
    """
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.environ.get("SENTRIQ_PERFORMANCE_MODEL_PATH")
        self.provider_name = "CatBoostPerformancePredictionProvider"
        self._model = None
        self._metadata = None
        self._load_status = "UNCONFIGURED"
        self._load_reason = "MODEL_ARTIFACT_NOT_CONFIGURED"

        if self.model_path:
            self._init_model()

    def _init_model(self):
        if not self.model_path or not os.path.exists(self.model_path):
            self._load_status = "UNCONFIGURED"
            self._load_reason = "MODEL_ARTIFACT_NOT_CONFIGURED"
            return

        # Attempt companion metadata load
        meta_path = self.model_path + ".json"
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            except Exception:
                self._metadata = None

        # Lazy CatBoost import & load
        try:
            import catboost as cb
            model = cb.CatBoostRegressor()
            model.load_model(self.model_path)
            self._model = model
            self._load_status = "READY"
            self._load_reason = None
        except Exception as e:
            self._model = None
            self._load_status = "ERROR"
            self._load_reason = f"MODEL_LOAD_FAILED: {str(e)}"

    def predict_performance(
        self,
        candidate: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict latency for an eligible PQC candidate.
        Does NOT predict throughput (predicted_throughput_ops_s remains None).
        """
        cand_name = candidate.get("algorithm") or candidate.get("candidate", "UNKNOWN")

        # Canonical output schema with clear status, reason, and warnings
        res = {
            "status": self._load_status,
            "reason": self._load_reason,
            "candidate": cand_name,
            "predicted_latency_us": None,
            "predicted_throughput_ops_s": None,  # MUST remain None (throughput model unavailable)
            "model_version": self._metadata.get("model_version") if self._metadata else None,
            "dataset_version": self._metadata.get("dataset_version") if self._metadata else None,
            "provider_name": self.provider_name,
            "benchmark_source": self._metadata.get("benchmark_source") if self._metadata else None,
            "evidence": [],
            "warnings": [self._load_reason] if self._load_reason else [],
            "missing_features": []
        }

        if self._load_status != "READY" or self._model is None:
            return res

        # Extract exact features using candidate adapter
        features, missing = PerformanceCandidateAdapter.extract_features(candidate, context)
        if missing:
            res["status"] = "UNCONFIGURED"
            res["reason"] = "MISSING_REQUIRED_MODEL_FEATURES"
            res["missing_features"] = missing
            res["warnings"] = [f"Missing required model features: {', '.join(missing)}"]
            return res

        try:
            feature_values = list(features.values())
            prediction = self._model.predict(feature_values)
            predicted_lat = float(prediction) if isinstance(prediction, (int, float)) else float(prediction[0])

            res["predicted_latency_us"] = round(predicted_lat, 2)
            res["evidence"].append(f"CatBoost predicted CPU latency: {res['predicted_latency_us']} µs.")
            return res
        except Exception as e:
            res["status"] = "ERROR"
            res["reason"] = f"INFERENCE_FAILED: {str(e)}"
            res["warnings"] = [f"INFERENCE_FAILED: {str(e)}"]
            return res
