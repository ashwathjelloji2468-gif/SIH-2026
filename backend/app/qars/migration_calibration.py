import os
import json
from typing import Dict, Any

CALIBRATION_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "knowledge",
    "data",
    "qars_migration_calibration.json"
)

_cached_calibration: Dict[str, Any] = {}


def load_migration_calibration() -> Dict[str, Any]:
    """
    Loads versioned migration complexity calibration data from qars_migration_calibration.json.
    """
    global _cached_calibration
    if _cached_calibration:
        return _cached_calibration

    if os.path.exists(CALIBRATION_FILE_PATH):
        with open(CALIBRATION_FILE_PATH, "r", encoding="utf-8") as f:
            _cached_calibration = json.load(f)
            return _cached_calibration

    # Fallback default dataset structure
    _cached_calibration = {
        "metadata": {
            "version": "SENTRIQ QARS Prototype Heuristic Migration Calibration v1",
            "source_type": "SENTRIQ_PROTOTYPE_HEURISTIC",
            "confidence": "PROVISIONAL"
        },
        "factor_weights": {
            "affected_files_count": 0.10,
            "affected_assets_count": 0.10,
            "dependency_count": 0.10,
            "protocol_impact_detected": 0.10,
            "replaceable_library_interface_count": 0.05,
            "vendor_kms_hsm_detected": 0.10,
            "vendor_dependency_count": 0.05,
            "pki_cert_dependency_count": 0.05,
            "testing_requirement_level": 0.10,
            "availability_impact": 0.05,
            "blast_radius_affected_nodes": 0.10,
            "business_criticality_score": 0.10
        },
        "max_bounds": {
            "affected_files_count": 20,
            "affected_assets_count": 10,
            "dependency_count": 10,
            "vendor_dependency_count": 5,
            "pki_cert_dependency_count": 5,
            "blast_radius_affected_nodes": 20
        }
    }
    return _cached_calibration
