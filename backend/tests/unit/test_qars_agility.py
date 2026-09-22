import pytest
from app.qars.agility import collect_crypto_agility_evidence, analyze_source_ast_for_agility
from app.qars.models import QARSCryptoAgilityEvidence
from app.qars.service import evaluate_artifact_qars


class MockEvidence:
    def __init__(self, source_file, detector_name):
        self.source_file = source_file
        self.detector_name = detector_name


class MockAsset:
    def __init__(self, asset_type="ALGORITHM", algorithm_name="AES-256", purpose="ENCRYPTION", evidence_items=None, extra_metadata=None):
        self.id = "mock-asset-1"
        self.asset_type = asset_type
        self.algorithm_name = algorithm_name
        self.purpose = purpose
        self.evidence_items = evidence_items or []
        self.extra_metadata = extra_metadata or {}


# ----------------------------------------------------------------------
# PHASE 3B.2 REGRESSION & PRECISION TESTS (1 - 18)
# ----------------------------------------------------------------------

def test_01_get_description_is_not_des():
    py_code = """
def get_description(destination_path: str) -> str:
    return f"Processing destination: {destination_path}"
"""
    ast_res = analyze_source_ast_for_agility(py_code, "utils/desc.py")
    assert ast_res["total_crypto_refs"] == 0
    assert ast_res["hard_coded_count"] == 0


def test_02_cryptonode_orm_model_is_not_crypto_evidence():
    py_code = """
def fetch_nodes(db):
    return db.query(CryptoNode).filter(CryptoNode.scan_id == "scan-123").all()
"""
    ast_res = analyze_source_ast_for_agility(py_code, "app/graph.py")
    assert ast_res["total_crypto_refs"] == 0
    assert ast_res["hard_coded_count"] == 0


def test_03_basescanner_is_not_crypto_abstraction():
    py_code = """
from abc import ABC, abstractmethod

class BaseScanner(ABC):
    @abstractmethod
    def scan(self, target_path: str):
        pass
"""
    ast_res = analyze_source_ast_for_agility(py_code, "app/scanners/base.py")
    assert len(ast_res["abstractions_found"]) == 0

    asset = MockAsset(extra_metadata={"source_code": py_code, "verified_scan": True})
    res = collect_crypto_agility_evidence(asset)
    assert res.crypto_abstraction_layer_presence is False
    assert res.crypto_abstraction_layer_status == "CONFIGURED"


def test_04_componentprovider_is_not_crypto_provider():
    py_code = """
from abc import ABC, abstractmethod

class ComponentProvider(ABC):
    @abstractmethod
    def get_components(self):
        pass

class RuleComponentProvider(ComponentProvider):
    def get_components(self):
        return ["rule1", "rule2"]
"""
    ast_res = analyze_source_ast_for_agility(py_code, "app/qars/policy.py")
    assert len(ast_res["replaceable_interfaces_found"]) == 0

    asset = MockAsset(extra_metadata={"source_code": py_code, "verified_scan": True})
    res = collect_crypto_agility_evidence(asset)
    assert res.replaceable_library_interface_count == 0
    assert res.replaceable_library_interface_status == "CONFIGURED"


def test_05_qarscalibrationprovider_is_not_crypto_provider():
    py_code = """
class QARSCalibrationProvider:
    def load_calibration_dataset(self, path: str):
        return {"version": 1}
"""
    ast_res = analyze_source_ast_for_agility(py_code, "app/qars/calibration.py")
    assert len(ast_res["abstractions_found"]) == 0
    assert len(ast_res["replaceable_interfaces_found"]) == 0


def test_06_generic_service_class_is_not_crypto_abstraction():
    py_code = """
from abc import ABC, abstractmethod

class UserService(ABC):
    @abstractmethod
    def get_user(self, user_id: str):
        pass
"""
    ast_res = analyze_source_ast_for_agility(py_code, "services/user_service.py")
    assert len(ast_res["abstractions_found"]) == 0


def test_07_generic_adapter_is_not_crypto_replaceability_evidence():
    py_code = """
class PaymentAdapter:
    def process_payment(self, amount: float):
        pass
"""
    ast_res = analyze_source_ast_for_agility(py_code, "adapters/payment.py")
    assert len(ast_res["replaceable_interfaces_found"]) == 0


def test_08_genuine_crypto_abstraction_is_detected():
    py_code = """
import hashlib
from abc import ABC, abstractmethod

class ICryptoProvider(ABC):
    @abstractmethod
    def encrypt(self, data: bytes) -> bytes:
        pass
"""
    ast_res = analyze_source_ast_for_agility(py_code, "crypto/provider.py")
    assert len(ast_res["abstractions_found"]) == 1
    assert "ICryptoProvider" in ast_res["abstractions_found"][0]


def test_09_genuine_crypto_provider_is_detected():
    py_code = """
import cryptography
from abc import ABC, abstractmethod

class JceCipherProvider(ABC):
    @abstractmethod
    def add_provider(self, provider_name: str):
        pass
"""
    ast_res = analyze_source_ast_for_agility(py_code, "crypto/jce_provider.py")
    assert len(ast_res["replaceable_interfaces_found"]) == 1


def test_10_paramiko_pkey_abstraction_is_detected():
    py_code = """
import paramiko
from abc import ABC, abstractmethod

class PKey(ABC):
    @abstractmethod
    def sign_ssh_data(self, data: bytes):
        pass
"""
    ast_res = analyze_source_ast_for_agility(py_code, "paramiko/pkey.py")
    assert len(ast_res["abstractions_found"]) == 1
    assert "PKey" in ast_res["abstractions_found"][0]


def test_11_pyca_ciphercontext_abstraction_is_detected():
    py_code = """
from cryptography.hazmat.primitives.ciphers import base
from abc import ABC, abstractmethod

class CipherContext(ABC):
    @abstractmethod
    def encrypt(self, data: bytes) -> bytes:
        pass
"""
    ast_res = analyze_source_ast_for_agility(py_code, "cryptography/ciphers/base.py")
    assert len(ast_res["abstractions_found"]) == 1
    assert "CipherContext" in ast_res["abstractions_found"][0]


def test_12_genuine_crypto_provider_backend_in_pyca_is_detected():
    py_code = """
import cryptography

class OpenSSLBackendProvider:
    def add_provider(self, name: str):
        pass
"""
    ast_res = analyze_source_ast_for_agility(py_code, "cryptography/hazmat/backends/openssl.py")
    assert len(ast_res["replaceable_interfaces_found"]) == 1


def test_13_two_signal_requirement_is_enforced():
    # Signal 1 only (Abstract class without crypto relevance) -> Fails
    py_code_sig1 = """
from abc import ABC, abstractmethod

class DataService(ABC):
    @abstractmethod
    def load((self):
        pass
"""
    ast_res1 = analyze_source_ast_for_agility(py_code_sig1, "data.py")
    assert len(ast_res1["abstractions_found"]) == 0

    # Signal 1 AND Signal 2 -> Passes
    py_code_both = """
from cryptography.hazmat.primitives import ciphers
from abc import ABC, abstractmethod

class DataEncryptionService(ABC):
    @abstractmethod
    def encrypt(self, data: bytes):
        pass
"""
    ast_res2 = analyze_source_ast_for_agility(py_code_both, "crypto_data.py")
    assert len(ast_res2["abstractions_found"]) == 1


def test_14_evidence_signals_are_preserved():
    py_code = """
import cryptography
from abc import ABC, abstractmethod

class CryptoWrapper(ABC):
    @abstractmethod
    def encrypt(self, data: bytes):
        pass
"""
    ast_res = analyze_source_ast_for_agility(py_code, "wrapper.py")
    assert len(ast_res["evidence_signals"]) == 1
    sig = ast_res["evidence_signals"][0]
    assert sig["file"] == "wrapper.py"
    assert "crypto_library_import" in sig["signals"]
    assert "crypto_method_detected" in sig["signals"]


def test_15_unknown_vs_verified_zero_semantics_remain_correct():
    # Scan unavailable / insufficient evidence -> None / UNCONFIGURED
    asset_unconf = MockAsset()
    res_unconf = collect_crypto_agility_evidence(asset_unconf)
    assert res_unconf.crypto_abstraction_layer_presence is None
    assert res_unconf.crypto_abstraction_layer_status == "UNCONFIGURED"

    # Verified scan + 0 found -> False / CONFIGURED
    asset_zero = MockAsset(extra_metadata={"verified_scan": True, "abstractions_found": []})
    res_zero = collect_crypto_agility_evidence(asset_zero)
    assert res_zero.crypto_abstraction_layer_presence is False
    assert res_zero.crypto_abstraction_layer_status == "CONFIGURED"


def test_16_existing_hard_coded_ratio_behavior_remains_correct():
    asset = MockAsset(extra_metadata={
        "hard_coded_count": 3,
        "total_crypto_references": 4
    })
    res = collect_crypto_agility_evidence(asset)
    assert res.hard_coded_algorithm_ratio == 0.75
    assert res.hard_coded_algorithm_ratio_status == "CONFIGURED"
    assert res.provenance["hard_coded_algorithm_ratio"] == "DERIVED_SYSTEM_ANALYSIS"


def test_17_no_final_agility_score_exists():
    asset = MockAsset()
    res = collect_crypto_agility_evidence(asset)
    assert not hasattr(res, "score")
    assert "score" not in res.dict()
    assert "CAR" not in res.dict()


def test_18_final_score_remains_equal_to_core_score():
    asset = {
        "id": "asset-precision-test",
        "algorithm": "RSA-2048",
        "asset_type": "ALGORITHM",
        "extra_metadata": {
            "x_years": 5.0,
            "data_sensitivity": 4.0,
            "exposure": 3.0,
            "verified_scan": True,
            "abstractions_found": ["ICryptoProvider"]
        }
    }
    res = evaluate_artifact_qars(asset=asset)
    assert res.crypto_agility_evidence is not None
    assert res.final_score >= res.base_score
    assert res.final_score <= 100.0
    assert res.adjustments.get("crypto_agility", 0.0) >= 0.0

