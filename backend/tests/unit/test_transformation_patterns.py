import os
import tempfile
from app.models.enums import CryptoPurpose, QuantumSafety, RecommendationCategory
from app.recommend.engine import RecommendationEngine
from app.migration.transformer import MigrationTransformer
from app.migration.sandbox import SandboxEnvironment

class MockAsset:
    def __init__(self, algorithm_name, purpose, asset_type="ALGORITHM", location="test_crypto.py"):
        self.algorithm_name = algorithm_name
        self.purpose = purpose
        self.asset_type = asset_type
        self.location = location

def test_rule_1_rsa_jwt_signer_digital_signature():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    assert rec["recommended_algorithm"] == "ML-DSA (FIPS 204)"
    assert rec["alternative_algorithm"] == "SLH-DSA (FIPS 205)"
    assert rec["transformation_pattern"] == "RSA_TO_ML_DSA"

    transformer = MigrationTransformer()
    with tempfile.TemporaryDirectory() as sandbox_dir:
        test_file = os.path.join(sandbox_dir, "test_crypto.py")
        with open(test_file, "w") as f:
            f.write("from cryptography.hazmat.primitives.asymmetric import rsa\nkey = rsa.generate_private_key(65537, 2048)\n")
        
        asset = MockAsset("RSA-2048", CryptoPurpose.DIGITAL_SIGNATURE)
        res = transformer.transform_sandbox_code(sandbox_dir, asset, rec)
        assert res["status"] == "TRANSFORMED"
        assert res["transformation_type"] == "RSA_TO_ML_DSA"
        assert res["target_pqc_candidate"] == "ML-DSA-65 (NIST FIPS 204)"


def test_rule_2_ecdsa_digital_signature():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="ECDSA",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    assert rec["recommended_algorithm"] == "ML-DSA (FIPS 204)"
    assert rec["transformation_pattern"] == "ECDSA_TO_ML_DSA"

    transformer = MigrationTransformer()
    with tempfile.TemporaryDirectory() as sandbox_dir:
        test_file = os.path.join(sandbox_dir, "test_crypto.py")
        with open(test_file, "w") as f:
            f.write("from cryptography.hazmat.primitives.asymmetric import ec\nkey = ec.generate_private_key(ec.SECP256R1())\n")
        
        asset = MockAsset("ECDSA", CryptoPurpose.DIGITAL_SIGNATURE)
        res = transformer.transform_sandbox_code(sandbox_dir, asset, rec)
        assert res["status"] == "TRANSFORMED"
        assert res["transformation_type"] == "ECDSA_TO_ML_DSA"


def test_rule_3_ecdh_key_establishment():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="ECDH",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    assert rec["recommended_algorithm"] == "ML-KEM (FIPS 203)"
    assert rec["transformation_pattern"] == "ECDH_TO_ML_KEM_HYBRID"

    transformer = MigrationTransformer()
    with tempfile.TemporaryDirectory() as sandbox_dir:
        test_file = os.path.join(sandbox_dir, "test_crypto.py")
        with open(test_file, "w") as f:
            f.write("from cryptography.hazmat.primitives.asymmetric import ec\npeer_key = ec.generate_private_key(ec.SECP256R1())\n")
        
        asset = MockAsset("ECDH", CryptoPurpose.KEY_ESTABLISHMENT)
        res = transformer.transform_sandbox_code(sandbox_dir, asset, rec)
        assert res["status"] == "TRANSFORMED"
        assert res["transformation_type"] == "ECDH_TO_ML_KEM_HYBRID"


def test_rule_4_aes_symmetric_encryption_retention():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="AES-128",
        purpose=CryptoPurpose.ENCRYPTION,
        quantum_safety=QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN
    )
    assert rec["category"] == RecommendationCategory.RETAIN_SYMMETRIC_CRYPTO
    assert rec["recommended_algorithm"] == "RETAIN_EXISTING"

    transformer = MigrationTransformer()
    with tempfile.TemporaryDirectory() as sandbox_dir:
        asset = MockAsset("AES-128", CryptoPurpose.ENCRYPTION)
        res = transformer.transform_sandbox_code(sandbox_dir, asset, rec)
        assert res["status"] == "NO_PQC_TRANSFORMATION_REQUIRED"
        assert res["transformation_type"] == "RETAIN_EXISTING_PRIMITIVE"


def test_rule_5_unknown_hsm_manual_review():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="CUSTOM_HSM_ALG",
        purpose=CryptoPurpose.UNKNOWN,
        quantum_safety=QuantumSafety.UNKNOWN
    )
    assert rec["category"] == RecommendationCategory.MANUAL_REVIEW
    assert rec["transformation_pattern"] == "MANUAL_REVIEW"

    transformer = MigrationTransformer()
    with tempfile.TemporaryDirectory() as sandbox_dir:
        asset = MockAsset("CUSTOM_HSM_ALG", CryptoPurpose.UNKNOWN)
        res = transformer.transform_sandbox_code(sandbox_dir, asset, rec)
        assert res["status"] == "MANUAL_REVIEW_REQUIRED"


if __name__ == "__main__":
    test_rule_1_rsa_jwt_signer_digital_signature()
    test_rule_2_ecdsa_digital_signature()
    test_rule_3_ecdh_key_establishment()
    test_rule_4_aes_symmetric_encryption_retention()
    test_rule_5_unknown_hsm_manual_review()
    print("ALL TRANSFORMATION PATTERN TESTS PASSED SUCCESSFULLY!")
