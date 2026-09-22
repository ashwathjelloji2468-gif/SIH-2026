import os
import json
from typing import Dict, Any

CALIBRATION_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "knowledge",
    "data",
    "qars_agility_calibration.json"
)

_cached_calibration: Dict[str, Any] = {}


def load_agility_calibration() -> Dict[str, Any]:
    """
    Loads versioned crypto-agility score calibration data from qars_agility_calibration.json.
    """
    global _cached_calibration
    if _cached_calibration:
        return _cached_calibration

    if os.path.exists(CALIBRATION_FILE_PATH):
        with open(CALIBRATION_FILE_PATH, "r", encoding="utf-8") as f:
            _cached_calibration = json.load(f)
            return _cached_calibration

    _cached_calibration = {
        "metadata": {
            "version": "SENTRIQ QARS Prototype Heuristic Agility Calibration v1",
            "source_type": "SENTRIQ_PROTOTYPE_HEURISTIC",
            "confidence": "PROVISIONAL"
        },
        "factor_weights": {
            "hard_coded_algorithm_ratio": 0.30,
            "crypto_abstraction_layer_presence": 0.35,
            "replaceable_library_interface_count": 0.20,
            "vendor_kms_hsm_detected": 0.05,
            "protocol_impact_detected": 0.10
        }
    }
    return _cached_calibration
