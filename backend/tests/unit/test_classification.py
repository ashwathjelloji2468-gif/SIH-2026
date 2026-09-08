import pytest
from app.normalization.crypto_asset_normalizer import (
    classify_crypto_asset,
    determine_quantum_safety,
    determine_asset_lifetime,
    determine_business_criticality,
)
from app.models.enums import AssetType, CryptoPurpose, QuantumSafety
from app.models.db_models import CryptoAsset


def test_classification_rsa():
    res = classify_crypto_asset("RSA-2048", key_size=2048, asset_type=AssetType.CERTIFICATE, purpose=CryptoPurpose.DIGITAL_SIGNATURE)
    assert res["quantum_safety"] == QuantumSafety.QUANTUM_VULNERABLE
    assert res["lifetime_label"] == "LONG_TERM"
    assert res["data_lifetime_years"] == 10.0
    assert res["business_criticality_label"] == "CRITICAL" or res["business_criticality_label"] == "HIGH"
    assert "Type: CERTIFICATE" in res["classification_summary"]


def test_classification_aes():
    res = classify_crypto_asset("AES-256", key_size=256, asset_type=AssetType.ALGORITHM, purpose=CryptoPurpose.ENCRYPTION)
    assert res["quantum_safety"] == QuantumSafety.QUANTUM_SAFE
    assert res["lifetime_label"] == "MEDIUM_TERM"
    assert res["data_lifetime_years"] == 7.0
    assert res["business_criticality_label"] in ["MEDIUM", "HIGH"]


def test_classification_vendor_managed():
    res = classify_crypto_asset("BLACKBOX-HSM", asset_type=AssetType.VENDOR_MANAGED)
    assert res["lifetime_label"] == "PERMANENT"
    assert res["data_lifetime_years"] == 20.0
    assert res["business_criticality_label"] == "CRITICAL"


def test_crypto_asset_properties():
    asset = CryptoAsset(
        name="test-cert",
        asset_type=AssetType.CERTIFICATE,
        algorithm_name="RSA-2048",
        key_size=2048,
        purpose=CryptoPurpose.AUTHENTICATION,
        location="cert.pem"
    )
    assert asset.data_lifetime_years == 10.0
    assert asset.lifetime_label == "LONG_TERM"
    assert asset.business_criticality_label in ["HIGH", "CRITICAL"]
    assert "Type: CERTIFICATE" in asset.classification_summary
