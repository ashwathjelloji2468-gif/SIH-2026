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
    # Empty stats fall back to default 3.0
    y_default = estimate_migration_time_from_stats()
    assert y_default == 3.0

    # Repo with 25 RSA/ECDSA assets, 10 legacy ciphers, and HSM
    y_complex = estimate_migration_time_from_stats(
        total_assets=35,
        total_rsa_ecc_assets=25,
        hardcoded_crypto_instances=5,
        legacy_ciphers_count=5,
        has_vendor_managed_or_hsm=True
    )
    # 1.0 (base) + 2.5 (RSA/ECC) + 0.5 (hardcoded+legacy) + 2.5 (HSM) + 0.5 (>20 assets) = 7.0
    assert y_complex >= 6.0 and y_complex <= 15.0


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
    assert y_val > 3.0


def test_build_dynamic_mosca_inputs():
    class DummyAsset:
        data_lifetime_years = 15.0
        algorithm_name = "RSA-4096"
        asset_type = AssetType.CERTIFICATE
        quantum_safety = QuantumSafety.QUANTUM_VULNERABLE

    asset = DummyAsset()
    x, y, z = build_dynamic_mosca_inputs(asset)

    assert x == 15.0
    assert y >= 1.0
    assert z == 2033


def test_calculate_mosca_urgency_backward_compatibility():
    # Calling with default parameters
    res = calculate_mosca_urgency()
    assert res["data_lifetime_years"] == 10.0
    assert res["migration_time_years"] == 3.0
    assert res["quantum_threat_horizon"] == 2033
    assert "urgency_level" in res
