import pytest
from app.risk.mosca import (
    calculate_mosca_analysis,
    estimate_migration_time_from_stats,
    estimate_migration_time_from_assets,
    build_dynamic_mosca_inputs,
    calculate_mosca_urgency,
)
from app.models.enums import AssetType, QuantumSafety


def test_estimate_migration_time_from_stats():
    # Canonical YEngine default STANDARD scenario is 10.0 years
    y_default = estimate_migration_time_from_stats()
    assert y_default == 10.0


def test_estimate_migration_time_from_assets():
    class DummyAsset:
        def __init__(self, alg, atype, qs):
            self.algorithm_name = alg
            self.asset_type = atype
            self.quantum_safety = qs
            self.data_lifetime_years = 10.0

    assets = [
        DummyAsset("RSA-2048", AssetType.CERTIFICATE, QuantumSafety.QUANTUM_VULNERABLE),
        DummyAsset("ECDSA-P256", AssetType.ALGORITHM, QuantumSafety.QUANTUM_VULNERABLE),
        DummyAsset("MD5", AssetType.ALGORITHM, QuantumSafety.QUANTUM_VULNERABLE),
        DummyAsset("AWS-KMS-SERVICE", AssetType.VENDOR_MANAGED, QuantumSafety.QUANTUM_SAFE),
    ]

    y_val = estimate_migration_time_from_assets(assets)
    assert y_val == 10.0


def test_build_dynamic_mosca_inputs():
    class DummyAsset:
        data_lifetime_years = 15.0
        algorithm_name = "RSA-4096"
        asset_type = AssetType.CERTIFICATE
        quantum_safety = QuantumSafety.QUANTUM_VULNERABLE

    asset = DummyAsset()
    x, y, z = build_dynamic_mosca_inputs(asset)

    assert x == 15.0
    assert y == 10.0
    assert z == 2036


def test_calculate_mosca_urgency_backward_compatibility():
    # Calling with default parameters
    res = calculate_mosca_urgency()
    assert res["data_lifetime_years"] == 20.0
    assert res["migration_time_years"] == 10.0
    assert res["quantum_threat_horizon"] == 2036
    assert "urgency_level" in res
