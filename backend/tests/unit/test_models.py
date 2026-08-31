import pytest
from app.models.enums import RiskLevel, AssetType, CryptoPurpose, QuantumSafety

def test_enums():
    assert RiskLevel.CRITICAL.value == "CRITICAL"
    assert AssetType.ALGORITHM.value == "ALGORITHM"
    assert CryptoPurpose.SIGNATURE.value == "SIGNATURE"
    assert QuantumSafety.QUANTUM_VULNERABLE.value == "QUANTUM_VULNERABLE"
