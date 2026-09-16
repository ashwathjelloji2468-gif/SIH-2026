import os
import tempfile
import pytest
from app.migration.sandbox import SandboxEnvironment
from app.migration.comparison import BeforeAfterComparer
from app.migration.transformer import MigrationTransformer
from app.migration.simulator import MigrationSimulator
from app.validation.validator import MigrationValidator
from app.models.enums import QuantumSafety, CryptoPurpose, AssetType, SimulationStatus
from app.models.db_models import Project, Scan, CryptoAsset, Recommendation

def test_1_baseline_working_isolation():
    with tempfile.TemporaryDirectory() as src_dir:
        fpath = os.path.join(src_dir, "test.py")
        with open(fpath, "w") as f:
            f.write("import rsa\n")

        sandbox = SandboxEnvironment(simulation_id="test_iso")
        working_dir = sandbox.prepare_sandbox(source_path=src_dir)
        baseline_dir = sandbox.baseline_dir

        assert baseline_dir != working_dir
        assert os.path.exists(baseline_dir)
        assert os.path.exists(working_dir)

        # Modify working_dir
        with open(os.path.join(working_dir, "test.py"), "a") as f:
            f.write("# modified\n")

        # Verify baseline_dir remains untouched
        with open(os.path.join(baseline_dir, "test.py"), "r") as f:
            content = f.read()
        assert content == "import rsa\n"

        sandbox.cleanup()

def test_2_original_repo_immutability():
    with tempfile.TemporaryDirectory() as src_dir:
        fpath = os.path.join(src_dir, "app.py")
        orig_content = "import rsa\nkey = rsa.generate_private_key(65537, 2048)\n"
        with open(fpath, "w") as f:
            f.write(orig_content)

        sandbox = SandboxEnvironment(simulation_id="test_immut")
        working_dir = sandbox.prepare_sandbox(source_path=src_dir)

        # Modify working dir
        with open(os.path.join(working_dir, "app.py"), "w") as f:
            f.write("from pqcrypto.sign import ml_dsa_65\n")

        # Original source directory must be 100% unchanged
        with open(fpath, "r") as f:
            after_content = f.read()
        assert after_content == orig_content
        sandbox.cleanup()

def test_3_path_boundary_validation():
    sandbox = SandboxEnvironment(simulation_id="test_path_boundary")
    working_dir = sandbox.prepare_sandbox()

    valid_file = os.path.join(working_dir, "clean.py")
    assert sandbox.validate_path_within_sandbox(valid_file, working_dir) is True

    with pytest.raises(ValueError, match="Path traversal attempt detected"):
        sandbox.validate_path_within_sandbox("/etc/passwd", working_dir)

    with pytest.raises(ValueError, match="Path traversal attempt detected"):
        sandbox.validate_path_within_sandbox(os.path.join(working_dir, "../secret.py"), working_dir)

    sandbox.cleanup()

def test_4_in_place_transformation_rsa_ml_dsa():
    transformer = MigrationTransformer()
    asset = CryptoAsset(
        id="ast_rsa",
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.SIGNATURE,
        asset_type=AssetType.ALGORITHM,
        location="signer.py"
    )
    rec = Recommendation(
        target_pqc_candidate="ML-DSA (FIPS 204)",
        category="MIGRATE_PQC"
    )

    with tempfile.TemporaryDirectory() as sbox_dir:
        fpath = os.path.join(sbox_dir, "signer.py")
        with open(fpath, "w") as f:
            f.write("from cryptography.hazmat.primitives.asymmetric import rsa\nkey = rsa.generate_private_key(65537, 2048)\n")

        res = transformer.transform_sandbox_code(sbox_dir, asset, rec)
        assert res["status"] == "TRANSFORMED"
        assert res["transformation_type"] == "RSA_TO_ML_DSA"

        with open(fpath, "r") as f:
            content = f.read()

        assert "ml_dsa" in content.lower()
        assert "rsa.generate_private_key" not in content
        assert "ML_DSA_65_PUBLIC_KEY" not in content  # No fake placeholders

def test_5_in_place_transformation_ecdh_ml_kem():
    transformer = MigrationTransformer()
    asset = CryptoAsset(
        id="ast_ecdh",
        algorithm_name="ECDH",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        asset_type=AssetType.ALGORITHM,
        location="key_ex.py"
    )
    rec = Recommendation(
        target_pqc_candidate="ML-KEM (FIPS 203)",
        category="MIGRATE_PQC"
    )

    with tempfile.TemporaryDirectory() as sbox_dir:
        fpath = os.path.join(sbox_dir, "key_ex.py")
        with open(fpath, "w") as f:
            f.write("from cryptography.hazmat.primitives.asymmetric import ec\nkey = ec.generate_private_key(ec.SECP256R1())\n")

        res = transformer.transform_sandbox_code(sbox_dir, asset, rec)
        assert res["status"] == "TRANSFORMED"
        assert res["transformation_type"] in ["ECDH_TO_ML_KEM", "ECDH_TO_ML_KEM_HYBRID"]

        with open(fpath, "r") as f:
            content = f.read()

        assert "ml_kem" in content.lower()
        assert "ec.generate_private_key" not in content
        assert "ML_KEM_768_PUBLIC_KEY" not in content  # No fake placeholders

def test_6_incompatible_pattern_rejection():
    transformer = MigrationTransformer()
    asset = CryptoAsset(
        id="ast_sig",
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.SIGNATURE,
        asset_type=AssetType.ALGORITHM
    )

    # Requesting ECDH/KEM pattern for signature asset -> BLOCKED
    res = transformer.transform_sandbox_code("/tmp", asset, None, requested_pattern="ECDH_TO_ML_KEM_HYBRID")
    assert res["status"] == "BLOCKED"
    assert "Incompatible" in res["unsupported_assumptions"][0]

def test_7_no_matching_vulnerable_op_manual_review():
    transformer = MigrationTransformer()
    asset = CryptoAsset(
        id="ast_nomatch",
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.SIGNATURE,
        asset_type=AssetType.ALGORITHM
    )

    with tempfile.TemporaryDirectory() as sbox_dir:
        fpath = os.path.join(sbox_dir, "helper.py")
        with open(fpath, "w") as f:
            f.write("# No crypto code here\ndef add(a, b):\n    return a + b\n")

        res = transformer.transform_sandbox_code(sbox_dir, asset, None)
        assert res["status"] == "MANUAL_REVIEW_REQUIRED"

def test_8_semantic_cryptographic_validation():
    validator = MigrationValidator()
    asset = CryptoAsset(id="a1", algorithm_name="RSA-2048", purpose=CryptoPurpose.SIGNATURE)
    rec = Recommendation(target_pqc_candidate="ML-DSA (FIPS 204)")

    with tempfile.TemporaryDirectory() as sbox_dir:
        fpath = os.path.join(sbox_dir, "app.py")
        # Transformed correctly: PQC present AND old RSA op removed
        with open(fpath, "w") as f:
            f.write("from pqcrypto.sign import ml_dsa_65  # ML-DSA-65 (FIPS 204)\nkey = ml_dsa_65.keypair()\n")

        t_res = {"status": "TRANSFORMED", "transformation_type": "RSA_TO_ML_DSA", "target_pqc_candidate": "ML-DSA (FIPS 204)"}
        val_res = validator.validate_simulation(sbox_dir, t_res, asset, rec)

        assert val_res["crypto_tests_passed"] is True
        assert val_res["unit_tests_passed"] is False  # Truthful: unit tests not run
        assert val_res["build_passed"] is False  # Truthful for NOT_CONFIGURED

def test_9_before_after_fingerprint_no_diff_fails():
    comparer = BeforeAfterComparer()
    with tempfile.TemporaryDirectory() as base_dir, tempfile.TemporaryDirectory() as work_dir:
        with open(os.path.join(base_dir, "same.py"), "w") as f:
            f.write("same content")
        with open(os.path.join(work_dir, "same.py"), "w") as f:
            f.write("same content")

        b_hash = comparer.compute_directory_fingerprint(base_dir)
        a_hash = comparer.compute_directory_fingerprint(work_dir)
        assert b_hash == a_hash  # No net diff
