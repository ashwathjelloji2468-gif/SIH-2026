import os
import json
from typing import Dict, Any

CALIBRATION_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "knowledge",
    "data",
    "qars_policy_calibration.json"
)

_cached_calibration: Dict[str, Any] = {}


def load_policy_calibration() -> Dict[str, Any]:
    """
    Loads versioned QARS policy calibration parameters from qars_policy_calibration.json.
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
            "version": "SENTRIQ QARS Prototype Heuristic Policy v1",
            "source_type": "SENTRIQ_PROTOTYPE_HEURISTIC",
            "confidence": "PROVISIONAL"
        },
        "max_adjustments": {
            "algorithm_risk": 15.0,
            "availability": 10.0,
            "crypto_agility": 15.0,
            "migration_complexity": 15.0
        },
        "total_max_adjustment_bound": 25.0
    }
    return _cached_calibration
