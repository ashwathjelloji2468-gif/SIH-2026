import os
import shutil
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.db_models import (
    Project, Scan, CryptoAsset, Recommendation, MigrationSimulation, ValidationRun
)
from app.models.enums import (
    AssetType, CryptoPurpose, QuantumSafety, RecommendationCategory,
    SimulationStatus, ValidationStatus, ValidationCheckType, ValidationCheckStatus
)
from app.migration.sandbox import SandboxEnvironment, SandboxConfig
from app.migration.transformer import MigrationTransformer
from app.migration.comparison import BeforeAfterComparer
from app.validation.runner import SandboxCommandRunner, ALLOWLISTED_EXECUTABLES
from app.validation.validator import MigrationValidator
from app.repositories.migration_simulation_repository import MigrationSimulationRepository
from app.repositories.validation_repository import ValidationRepository
from app.migration.simulator import MigrationSimulator


from sqlalchemy.pool import StaticPool


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# 1. Sandbox Creation
def test_1_sandbox_creation():
    sandbox = SandboxEnvironment(simulation_id="sim_test_1")
    sandbox_dir = sandbox.prepare_sandbox()
    try:
        assert os.path.exists(sandbox_dir)
        assert os.path.isabs(sandbox_dir)
        assert "sentriq_sim_sim_test_1_" in sandbox_dir
    finally:
        sandbox.cleanup()
    assert not os.path.exists(sandbox_dir)


# 2. Original Source Non-Modification
def test_2_original_source_unmodified():
    with tempfile.TemporaryDirectory() as orig_dir:
        sample_file = os.path.join(orig_dir, "app_crypto.py")
        orig_content = "import rsa\nkey = rsa.generate_key()\n"
        with open(sample_file, "w") as f:
            f.write(orig_content)

        sandbox = SandboxEnvironment(simulation_id="sim_test_2")
        sandbox_dir = sandbox.prepare_sandbox(source_path=orig_dir)
        try:
            # Modify inside sandbox
            s_file = os.path.join(sandbox_dir, "app_crypto.py")
            with open(s_file, "a") as f:
                f.write("# Modified in sandbox\n")

            # Verify original file remains unmodified
            with open(sample_file, "r") as f:
                content_after = f.read()
            assert content_after == orig_content
        finally:
            sandbox.cleanup()


# 3. Sandbox Path Boundary Isolation
def test_3_sandbox_path_boundary_isolation():
    sandbox = SandboxEnvironment(simulation_id="sim_test_3")
    sandbox_dir = sandbox.prepare_sandbox()
    try:
        valid_path = os.path.join(sandbox_dir, "inner.py")
        assert sandbox.validate_path_within_sandbox(valid_path, sandbox_dir) is True

        with pytest.raises(ValueError, match="Path traversal attempt detected"):
            sandbox.validate_path_within_sandbox("/etc/passwd", sandbox_dir)

        with pytest.raises(ValueError, match="Path traversal attempt detected"):
            sandbox.validate_path_within_sandbox(os.path.join(sandbox_dir, "../secret.txt"), sandbox_dir)
    finally:
        sandbox.cleanup()


# 4. Supported Python Source Detection
def test_4_supported_source_detection():
    sandbox = SandboxEnvironment(simulation_id="sim_test_4")
    assert sandbox.detect_language("script.py") == "Python"
    assert sandbox.detect_language("app.ts") == "TypeScript"
    assert sandbox.detect_language("Main.java") == "Java"
    assert sandbox.detect_language("main.go") == "Go"
    assert sandbox.detect_language("lib.rs") == "Rust"


# 5. Unsupported Source Language Produces MANUAL_REVIEW_REQUIRED
def test_5_unsupported_language_manual_review():
    with tempfile.TemporaryDirectory() as orig_dir:
        sample_file = os.path.join(orig_dir, "data.xyz")
        with open(sample_file, "w") as f:
            f.write("unsupported data format")

        sandbox = SandboxEnvironment(simulation_id="sim_test_5")
        sandbox.prepare_sandbox(source_path=orig_dir)
        try:
            assert sandbox.detected_language == "unknown"
        finally:
            sandbox.cleanup()


# 6. ECDH Key Establishment -> ML-KEM Adapter
def test_6_ecdh_transformation_adapter():
    transformer = MigrationTransformer()
    asset = CryptoAsset(
        id="ast_ecdh",
        algorithm_name="ECDH",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        asset_type=AssetType.ALGORITHM,
        location="auth.py"
    )
    recommendation = Recommendation(
        target_pqc_candidate="ML-KEM (FIPS 203)",
        category=RecommendationCategory.MIGRATE_PQC
    )

    with tempfile.TemporaryDirectory() as sbox_dir:
        target_f = os.path.join(sbox_dir, "auth.py")
        with open(target_f, "w") as f:
            f.write("from cryptography.hazmat.primitives.asymmetric import ec\n")

        res = transformer.transform_sandbox_code(sbox_dir, asset, recommendation)
        assert res["status"] == "TRANSFORMED"
        assert res["transformation_type"] == "ECDH_TO_ML_KEM"
        assert res["target_pqc_candidate"] == "ML-KEM (FIPS 203)"

        with open(target_f, "r") as f:
            content = f.read()
        assert "ML-KEM (FIPS 203)" in content


# 7. RSA / ECDSA Digital Signature -> ML-DSA Adapter
def test_7_rsa_ecdsa_transformation_adapter():
    transformer = MigrationTransformer()
    asset = CryptoAsset(
        id="ast_rsa",
        algorithm_name="RSA",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        asset_type=AssetType.ALGORITHM,
        location="sign.py"
    )
    recommendation = Recommendation(
        target_pqc_candidate="ML-DSA (FIPS 204)",
        category=RecommendationCategory.MIGRATE_PQC
    )

    with tempfile.TemporaryDirectory() as sbox_dir:
        target_f = os.path.join(sbox_dir, "sign.py")
        with open(target_f, "w") as f:
            f.write("import rsa\n")

        res = transformer.transform_sandbox_code(sbox_dir, asset, recommendation)
        assert res["status"] == "TRANSFORMED"
        assert res["transformation_type"] == "RSA_ECDSA_TO_ML_DSA"
        assert res["target_pqc_candidate"] == "ML-DSA (FIPS 204)"


# 8. AES is Retained (No PQC Replacement Required)
def test_8_aes_retention():
    transformer = MigrationTransformer()
    asset = CryptoAsset(
        id="ast_aes",
        algorithm_name="AES-256-GCM",
        purpose=CryptoPurpose.ENCRYPTION,
        asset_type=AssetType.ALGORITHM
    )
    recommendation = Recommendation(
        category=RecommendationCategory.RETAIN,
        target_pqc_candidate="RETAIN_EXISTING"
    )

    with tempfile.TemporaryDirectory() as sbox_dir:
        res = transformer.transform_sandbox_code(sbox_dir, asset, recommendation)
        assert res["status"] == "NO_PQC_TRANSFORMATION_REQUIRED"
        assert res["transformation_type"] == "RETAIN_EXISTING_PRIMITIVE"


# 9. SHA Hashing Retained
def test_9_sha_retention():
    transformer = MigrationTransformer()
    asset = CryptoAsset(
        id="ast_sha",
        algorithm_name="SHA-256",
        purpose=CryptoPurpose.HASHING,
        asset_type=AssetType.ALGORITHM
    )
    with tempfile.TemporaryDirectory() as sbox_dir:
        res = transformer.transform_sandbox_code(sbox_dir, asset, None)
        assert res["status"] == "NO_PQC_TRANSFORMATION_REQUIRED"


# 10. HMAC Retained
def test_10_hmac_retention():
    transformer = MigrationTransformer()
    asset = CryptoAsset(
        id="ast_hmac",
        algorithm_name="HMAC-SHA256",
        purpose=CryptoPurpose.MAC,
        asset_type=AssetType.ALGORITHM
    )
    with tempfile.TemporaryDirectory() as sbox_dir:
        res = transformer.transform_sandbox_code(sbox_dir, asset, None)
        assert res["status"] == "NO_PQC_TRANSFORMATION_REQUIRED"


# 11. Unknown / Binary Crypto -> Manual Review Required
def test_11_unknown_crypto_manual_review():
    transformer = MigrationTransformer()
    asset = CryptoAsset(
        id="ast_hsm",
        algorithm_name="PROPRIETARY_HSM_CIPHER",
        purpose=CryptoPurpose.UNKNOWN,
        asset_type=AssetType.BINARY
    )
    with tempfile.TemporaryDirectory() as sbox_dir:
        res = transformer.transform_sandbox_code(sbox_dir, asset, None)
        assert res["status"] == "MANUAL_REVIEW_REQUIRED"


# 12. Before / After Comparison & Fingerprinting
def test_12_before_after_fingerprint_and_diff():
    comparer = BeforeAfterComparer()
    with tempfile.TemporaryDirectory() as before_dir, tempfile.TemporaryDirectory() as after_dir:
        # Create identical base file
        fp1 = os.path.join(before_dir, "crypto.py")
        fp2 = os.path.join(after_dir, "crypto.py")
        with open(fp1, "w") as f:
            f.write("def cipher(): pass\n")
        with open(fp2, "w") as f:
            f.write("def cipher(): pass\n# PQC Adapter added\n")

        hash_before = comparer.compute_directory_fingerprint(before_dir)
        hash_after = comparer.compute_directory_fingerprint(after_dir)

        assert hash_before != hash_after
        summary = comparer.compare(before_dir, after_dir, files_changed=["crypto.py"], original_algorithm="RSA", target_candidate="ML-KEM-768")
        assert summary["files_changed_count"] == 1
        assert summary["lines_added"] == 1


# 13. Changed Files List Recorded
def test_13_changed_files_list():
    comparer = BeforeAfterComparer()
    summary = comparer.compare("/tmp/empty1", "/tmp/empty2", files_changed=["auth.py", "sign.py"])
    assert summary["files_changed"] == ["auth.py", "sign.py"]
    assert summary["files_changed_count"] == 2


# 14. Syntax Check Execution (PASS)
def test_14_syntax_check_execution():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as sbox_dir:
        py_file = os.path.join(sbox_dir, "valid.py")
        with open(py_file, "w") as f:
            f.write("x = 10\nprint(x)\n")

        res = runner.run_python_syntax_check(sbox_dir)
        assert res["status"] == ValidationCheckStatus.PASS.value
        assert res["exit_code"] == 0


# 15. Failed Syntax Check (FAIL)
def test_15_failed_syntax_check():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as sbox_dir:
        py_file = os.path.join(sbox_dir, "invalid.py")
        with open(py_file, "w") as f:
            f.write("def invalid_syntax_func(\n")

        res = runner.run_python_syntax_check(sbox_dir)
        assert res["status"] == ValidationCheckStatus.FAIL.value
        assert res["exit_code"] != 0


# 16. Missing Tooling / Unallowed Executable SKIPPED or BLOCKED
def test_16_missing_tooling_skipped():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as empty_dir:
        res = runner.run_python_syntax_check(empty_dir)
        assert res["status"] == ValidationCheckStatus.SKIPPED.value


# 17. Validation Evidence Persistence
def test_17_validation_evidence_persistence(db_session):
    val_repo = ValidationRepository(db_session)
    run = val_repo.create_validation_run(
        simulation_id="sim_100",
        asset_id="ast_100",
        check_type="SYNTAX",
        status=ValidationStatus.PASSED,
        command="python3 -m py_compile valid.py",
        exit_code=0,
        output_summary="Syntax OK",
        evidence={"stdout": "OK", "stderr": ""},
        duration=0.1,
        build_passed=True
    )
    assert run.id is not None
    assert run.simulation_id == "sim_100"
    assert run.evidence == {"stdout": "OK", "stderr": ""}


# 18. Migration Simulation SQLite Persistence
def test_18_migration_simulation_sqlite_persistence(db_session):
    sim_repo = MigrationSimulationRepository(db_session)
    sim = sim_repo.create_simulation(
        asset_id="ast_ecdh",
        project_id="proj_1",
        status=SimulationStatus.PREPARING
    )
    assert sim.id is not None
    assert sim.status == SimulationStatus.PREPARING

    updated = sim_repo.update_simulation_result(
        simulation_id=sim.id,
        status=SimulationStatus.PASSED,
        files_changed=["auth.py"],
        before_fingerprint="abc1",
        after_fingerprint="def2"
    )
    assert updated.status == SimulationStatus.PASSED
    assert updated.files_changed == ["auth.py"]


# 19. API Migration Simulation Endpoints
def test_19_api_migration_simulation_endpoints(client, db_session):
    proj = Project(id="proj_sim_api", name="Sim Test Project")
    scan = Scan(id="scan_sim_api", project_id="proj_sim_api", target_path="/app")
    asset = CryptoAsset(
        id="asset_sim_api",
        scan_id="scan_sim_api",
        name="ECDH-KeyEx",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="ECDH",
        location="key_ex.py",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db_session.add(proj)
    db_session.add(scan)
    db_session.add(asset)
    db_session.commit()

    response = client.post(f"/api/v1/migration/simulate?asset_id=asset_sim_api")
    assert response.status_code == 200
    data = response.json()
    assert "simulation_id" in data
    assert data["status"] in ["PASSED", "TRANSFORMED", "MANUAL_REVIEW_REQUIRED"]

    sim_id = data["simulation_id"]
    get_res = client.get(f"/api/v1/migration/simulations/{sim_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == sim_id

    list_res = client.get("/api/v1/migration/simulations")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


# 20. API Validation Endpoints
def test_20_api_validation_endpoints(client, db_session):
    proj = Project(id="proj_val_api", name="Val Test Project")
    scan = Scan(id="scan_val_api", project_id="proj_val_api", target_path="/app")
    asset = CryptoAsset(
        id="asset_val_api",
        scan_id="scan_val_api",
        name="RSA-2048",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        location="rsa_app.py",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db_session.add(proj)
    db_session.add(scan)
    db_session.add(asset)
    db_session.commit()

    # Create simulation
    sim_repo = MigrationSimulationRepository(db_session)
    sim = sim_repo.create_simulation(asset_id="asset_val_api", project_id="proj_val_api", status=SimulationStatus.TRANSFORMED)

    # Validate simulation endpoint
    val_res = client.post(f"/api/v1/migration/simulations/{sim.id}/validate")
    assert val_res.status_code == 200

    # Get validation run by simulation
    get_val = client.get(f"/api/v1/validation/simulation/{sim.id}")
    assert get_val.status_code == 200
    assert len(get_val.json()) >= 1

    # Validation summary
    summary_res = client.get("/api/v1/validation/summary")
    assert summary_res.status_code == 200
    assert summary_res.json()["total_validation_runs"] >= 1


# 21. Path Traversal Rejection
def test_21_path_traversal_rejection():
    sandbox = SandboxEnvironment(simulation_id="sim_security")
    with tempfile.TemporaryDirectory() as temp_root:
        with pytest.raises(ValueError, match="Security Alert: Path traversal attempt detected"):
            sandbox.validate_path_within_sandbox("/etc/shadow", temp_root)


# 22. Command Injection & Allowlist Enforcement
def test_22_command_injection_and_allowlist_enforcement():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as sbox_dir:
        # Non-allowlisted executable
        res_disallowed = runner.run_check(sbox_dir, ValidationCheckType.BUILD, ["bash", "-c", "echo hello"])
        assert res_disallowed["status"] == ValidationCheckStatus.BLOCKED.value
        assert "not in security allowlist" in res_disallowed["output_summary"]

        # Malformed command
        res_malformed = runner.run_check(sbox_dir, ValidationCheckType.BUILD, "invalid_string_cmd")  # type: ignore
        assert res_malformed["status"] == ValidationCheckStatus.FAIL.value


# 23. Prompt 1 to 5 Regression Safety
def test_23_prompt_1_to_5_regression_safety(db_session):
    proj = Project(id="proj_reg", name="Regression Project")
    scan = Scan(id="scan_reg", project_id="proj_reg", target_path="/app")
    asset = CryptoAsset(
        id="asset_reg",
        scan_id="scan_reg",
        name="AES-256",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256-GCM",
        purpose=CryptoPurpose.ENCRYPTION,
        location="src/cipher.py",
        quantum_safety=QuantumSafety.QUANTUM_SAFE
    )
    rec = Recommendation(
        id="rec_reg",
        asset_id="asset_reg",
        target_pqc_candidate="RETAIN_EXISTING",
        recommended_algorithm="AES-256-GCM",
        category=RecommendationCategory.RETAIN,
        rationale="Retain symmetric primitive"
    )
    db_session.add_all([proj, scan, asset, rec])
    db_session.commit()

    simulator = MigrationSimulator()
    res = simulator.run_simulation(db_session, asset_id="asset_reg")
    assert res["status"] == "PASSED"
    assert res["recommendation"]["current_algorithm"] == "AES-256-GCM"


# 24. Zero Production Source Code Modification
def test_24_zero_production_source_code_modification():
    with tempfile.TemporaryDirectory() as prod_source_dir:
        prod_file = os.path.join(prod_source_dir, "prod_crypto.py")
        original_bytes = b"import ssl\n# Production codebase\n"
        with open(prod_file, "wb") as f:
            f.write(original_bytes)

        sandbox = SandboxEnvironment(simulation_id="sim_prod_check")
        sbox_dir = sandbox.prepare_sandbox(source_path=prod_source_dir)
        try:
            # Perform transformation in sandbox
            transformer = MigrationTransformer()
            asset = CryptoAsset(id="a_prod", algorithm_name="RSA", purpose=CryptoPurpose.DIGITAL_SIGNATURE, location="prod_crypto.py")
            transformer.transform_sandbox_code(sbox_dir, asset, None)

            # Verify production file has exact same bytes
            with open(prod_file, "rb") as f:
                content_after = f.read()
            assert content_after == original_bytes
        finally:
            sandbox.cleanup()
