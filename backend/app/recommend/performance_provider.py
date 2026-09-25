import os
import json
import math
from typing import Dict, Any, List, Optional, Tuple

FEATURE_COLUMNS = [
    "algorithm",
    "security_level",
    "security_level_bits",
    "text_size_kb",
    "text_length_bytes",
    "primitive",
    "ciphertext_length",
    "signature_length",
    "overhead_bytes",
    "shared_secret_length",
]


class PerformanceCandidateAdapter:
    """
    Adapter converting SENTRIQ candidate and application context into
    the exact 10-feature schema required by the PQC performance model.
    """
    @staticmethod
    def extract_features(
        candidate: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Extract exact 10-feature schema for KEM or Signature models without fabricating missing values.
        Returns (feature_dict, list_of_missing_features).
        """
        cand_name = candidate.get("algorithm") or candidate.get("candidate")
        primitive_raw = (candidate.get("primitive") or "").upper()
        sec_level = candidate.get("security_level")
        ciphertext_size = candidate.get("ciphertext_size_bytes") if candidate.get("ciphertext_size_bytes") is not None else candidate.get("ciphertext_length")
        signature_size = candidate.get("signature_size_bytes") if candidate.get("signature_size_bytes") is not None else candidate.get("signature_length")
        shared_secret_size = candidate.get("shared_secret_bytes") if candidate.get("shared_secret_bytes") is not None else candidate.get("shared_secret_length")

        ctx = context or {}
        text_len = ctx.get("text_length_bytes") if ctx.get("text_length_bytes") is not None else (
            ctx.get("payload_size_bytes") if ctx.get("payload_size_bytes") is not None else ctx.get("message_size_bytes")
        )

        missing_features = []

        if not cand_name:
            missing_features.append("algorithm")

        if sec_level is None:
            missing_features.append("security_level")

        if text_len is None:
            missing_features.append("text_length_bytes")
            missing_features.append("text_size_kb")

        prim_str = None
        if "KEY_ESTABLISHMENT" in primitive_raw or "KEM" in primitive_raw:
            prim_str = "KEM"
            if ciphertext_size is None:
                missing_features.append("ciphertext_length")
        elif "DIGITAL_SIGNATURE" in primitive_raw or "SIGNATURE" in primitive_raw:
            prim_str = "SIGNATURE"
            if signature_size is None:
                missing_features.append("signature_length")
        else:
            missing_features.append("primitive")

        if missing_features:
            return None, missing_features

        sec_bits_map = {1: 128, 2: 128, 3: 192, 4: 192, 5: 256}
        sec_bits = sec_bits_map.get(sec_level, 128)
        text_size_kb = round(text_len / 1024.0, 4)

        nan_val = float("nan")

        if prim_str == "KEM":
            c_len = ciphertext_size
            s_len = nan_val
            overhead = ciphertext_size
            if shared_secret_size is not None:
                ss_len = shared_secret_size
            elif cand_name in ["ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"]:
                # Proven by standard specification: 32-byte shared secret (NIST FIPS 203 Section 1.1 / Table 2)
                ss_len = 32
            elif cand_name in ["Kyber512", "Kyber768", "Kyber1024"]:
                # Proven by standard specification: 32-byte shared secret (CRYSTALS-Kyber NIST Round 3 Specification)
                ss_len = 32
            elif cand_name in ["BIKE", "HQC"]:
                # Proven by standard specification: 32-byte shared secret (BIKE / HQC NIST Round 4 Specifications)
                ss_len = 32
            else:
                missing_features.append("shared_secret_length")
                return None, missing_features
        else:  # SIGNATURE
            c_len = nan_val
            s_len = signature_size
            overhead = signature_size
            ss_len = nan_val

        features = {
            "algorithm": cand_name,
            "security_level": sec_level,
            "security_level_bits": sec_bits,
            "text_size_kb": text_size_kb,
            "text_length_bytes": text_len,
            "primitive": prim_str,
            "ciphertext_length": c_len,
            "signature_length": s_len,
            "overhead_bytes": overhead,
            "shared_secret_length": ss_len,
        }

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
        if not os.path.exists(meta_path):
            self._load_status = "ERROR"
            self._load_reason = "INVALID_MODEL_ARTIFACT: Companion metadata JSON file missing"
            return

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)
        except Exception as e:
            self._metadata = None
            self._load_status = "ERROR"
            self._load_reason = f"INVALID_MODEL_ARTIFACT: Failed to parse metadata JSON: {str(e)}"
            return

        # Validate target metadata and inverse transformation compatibility
        target = self._metadata.get("training_target") or self._metadata.get("target")
        transform = self._metadata.get("prediction_inverse_transform")

        valid_targets = ["log1p(latency_us)", "latency_us", None]
        valid_transforms = ["expm1", "identity", None]

        if (target not in valid_targets) or (transform not in valid_transforms):
            self._load_status = "ERROR"
            self._load_reason = f"INVALID_MODEL_ARTIFACT: Unrecognized target '{target}' or inverse transform '{transform}'"
            return

        # Lazy CatBoost import & load
        try:
            import catboost as cb
            model = cb.CatBoostRegressor()
            model.load_model(self.model_path)

            # Validate feature schema if model provides feature_names_
            if hasattr(model, "feature_names_") and model.feature_names_:
                if list(model.feature_names_) != FEATURE_COLUMNS:
                    self._load_status = "ERROR"
                    self._load_reason = f"INVALID_MODEL_ARTIFACT: Feature schema mismatch. Expected {FEATURE_COLUMNS}, got {model.feature_names_}"
                    return

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
        Predict latency for an eligible PQC candidate using exact 10-column schema.
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

        # Extract exact 10 features using candidate adapter
        features, missing = PerformanceCandidateAdapter.extract_features(candidate, context)
        if missing:
            res["status"] = "UNCONFIGURED"
            res["reason"] = "MISSING_REQUIRED_MODEL_FEATURES"
            res["missing_features"] = missing
            res["warnings"] = [f"Missing required model features: {', '.join(missing)}"]
            return res

        try:
            import pandas as pd
            input_df = pd.DataFrame([features], columns=FEATURE_COLUMNS)
            prediction = self._model.predict(input_df)
        except Exception:
            try:
                prediction = self._model.predict(list(features.values()))
            except Exception as e:
                res["status"] = "ERROR"
                res["reason"] = f"INFERENCE_FAILED: {str(e)}"
                res["warnings"] = [f"INFERENCE_FAILED: {str(e)}"]
                return res

        try:
            raw_lat = float(prediction) if isinstance(prediction, (int, float)) else float(prediction[0])

            # Apply inverse transformation based on metadata
            transform = self._metadata.get("prediction_inverse_transform") if self._metadata else None
            target = (self._metadata.get("training_target") or self._metadata.get("target")) if self._metadata else None

            if transform == "expm1" or target == "log1p(latency_us)":
                predicted_lat = math.expm1(raw_lat)
            else:
                predicted_lat = raw_lat

            res["predicted_latency_us"] = round(predicted_lat, 2)
            res["evidence"].append(f"CatBoost predicted CPU latency: {res['predicted_latency_us']} µs.")
            return res
        except Exception as e:
            res["status"] = "ERROR"
            res["reason"] = f"INFERENCE_FAILED: {str(e)}"
            res["warnings"] = [f"INFERENCE_FAILED: {str(e)}"]
            return res
