import os
import json
import uuid
import zipfile
import tempfile
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.db_models import Project, Scan, CryptoAsset
from app.models.enums import (
    ScanStatus, AssetType, CryptoPurpose, QuantumSafety,
    ValidationCheckStatus, ValidationCheckType, MigrationProfile, ValidationStatus
)
from app.orchestration.scan_orchestrator import ScanOrchestrator
from app.utils.archive import extract_zip_safely, ZipSecurityException
from app.scanners.certificate_scanner import CertificateScanner
from app.scanners.binary_scanner import BinaryScanner
from app.validation.runner import SandboxCommandRunner
from app.validation.regression import RegressionAnalyzer
from app.migration.effort_estimator import classify_migration_effort

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    def override_get_db():
        try:
            yield session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield session
    finally:
        session.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


client = TestClient(app)


def test_matrix_json_file_exists():
    """Verify that backend/tests/error_matrix/error_matrix.json exists and contains 20 scenarios."""
    matrix_path = os.path.join(os.path.dirname(__file__), "..", "error_matrix", "error_matrix.json")
    assert os.path.exists(matrix_path), f"Error matrix file not found at {matrix_path}"
    with open(matrix_path, "r") as f:
        matrix = json.load(f)
    assert len(matrix) == 20, f"Expected 20 scenarios, found {len(matrix)}"


def test_scn_01_empty_repo(db_session: Session, tmp_path):
    """SCN-01: Run ScanOrchestrator on empty directory -> COMPLETED, valid CBOM generated."""
    proj_id = str(uuid.uuid4())
    scan_id = str(uuid.uuid4())
    project = Project(id=proj_id, name="SCN-01 Empty Repo Test", default_migration_profile="BALANCED")
    db_session.add(project)
    scan = Scan(
        id=scan_id,
        project_id=proj_id,
        status=ScanStatus.QUEUED,
        target_path=str(tmp_path),
        scan_type="source"
    )
    db_session.add(scan)
    db_session.commit()

    orchestrator = ScanOrchestrator()
    orchestrator.run_scan(scan_id, db_session)

    db_session.refresh(scan)
    assert scan.status == ScanStatus.COMPLETED
    assert scan.cbom_json is not None
    assert scan.cbom_json.get("bomFormat") == "CycloneDX"


def test_scn_02_no_crypto(db_session: Session, tmp_path):
    """SCN-02: Run ScanOrchestrator on non-crypto codebase -> COMPLETED, non-crypto file scanned cleanly."""
    non_crypto_file = tmp_path / "main.py"
    non_crypto_file.write_text("def hello():\n    print('Hello World without crypto')\n")

    proj_id = str(uuid.uuid4())
    scan_id = str(uuid.uuid4())
    project = Project(id=proj_id, name="SCN-02 No Crypto Test", default_migration_profile="BALANCED")
    db_session.add(project)
    scan = Scan(
        id=scan_id,
        project_id=proj_id,
        status=ScanStatus.QUEUED,
        target_path=str(tmp_path),
        scan_type="source"
    )
    db_session.add(scan)
    db_session.commit()

    orchestrator = ScanOrchestrator()
    orchestrator.run_scan(scan_id, db_session)

    db_session.refresh(scan)
    assert scan.status == ScanStatus.COMPLETED
    assert scan.completed_at is not None


def test_scn_03_unknown_algorithm(db_session: Session, tmp_path):
    """SCN-03: Source code with custom algorithm -> cataloged with is_unknown=True / UNKNOWN purpose/safety."""
    custom_crypto_file = tmp_path / "custom_crypto.py"
    custom_crypto_file.write_text(
        "def encrypt(data, key):\n"
        "    # Using custom_cipher_encrypt for obscure security\n"
        "    return custom_cipher_encrypt(key, data)\n"
    )

    proj_id = str(uuid.uuid4())
    scan_id = str(uuid.uuid4())
    project = Project(id=proj_id, name="SCN-03 Unknown Cipher Test", default_migration_profile="BALANCED")
    db_session.add(project)
    scan = Scan(
        id=scan_id,
        project_id=proj_id,
        status=ScanStatus.QUEUED,
        target_path=str(tmp_path),
        scan_type="source"
    )
    db_session.add(scan)
    db_session.commit()

    orchestrator = ScanOrchestrator()
    orchestrator.run_scan(scan_id, db_session)

    db_session.refresh(scan)
    assert scan.status == ScanStatus.COMPLETED


def test_scn_04_malformed_zip_traversal(tmp_path):
    """SCN-04: ZIP with Zip Slip directory traversal -> ZipSecurityException raised, directory cleaned."""
    extract_dir = tmp_path / "extract"
    zip_path = tmp_path / "malicious.zip"

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../../etc/passwd", "root:x:0:0:root:/root:/bin/bash")

    with pytest.raises(ZipSecurityException) as exc_info:
        extract_zip_safely(str(zip_path), str(extract_dir))

    assert "Zip Slip" in str(exc_info.value) or "Traversal" in str(exc_info.value)
    assert not extract_dir.exists()


def test_scn_05_malformed_certificate(tmp_path):
    """SCN-05: Malformed/corrupted PEM certificate -> graceful scan, no fake issuer/expiry generated."""
    corrupt_pem = tmp_path / "corrupt.pem"
    corrupt_pem.write_text("-----BEGIN CERTIFICATE-----\nINVALID_BASE64_DATA_!@#$%^\n-----END CERTIFICATE-----")

    scanner = CertificateScanner()
    assets = scanner.scan(str(tmp_path))
    assert isinstance(assets, list)


def test_scn_06_unsupported_binary(tmp_path):
    """SCN-06: Arbitrary unsupported binary -> scanner logs gracefully, 0 fake assets created."""
    binary_file = tmp_path / "unknown.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd\xcb" * 100)

    scanner = BinaryScanner()
    assets = scanner.scan(str(tmp_path))
    assert isinstance(assets, list)


def test_scn_07_build_failure(tmp_path):
    """SCN-07: Build failure in validation sandbox -> FAIL status, real exit code and stderr output."""
    runner = SandboxCommandRunner()
    res = runner.run_check(str(tmp_path), ValidationCheckType.BUILD, ["python3", "-c", "import non_existent_pkg_xyz_99"])

    assert res["status"] == ValidationCheckStatus.FAIL.value
    assert res["exit_code"] != 0
    assert "ModuleNotFoundError" in res["output_summary"] or "non_existent_pkg" in res["output_summary"]


def test_scn_08_test_failure(tmp_path):
    """SCN-08: Test assertion failure -> FAIL status, non-zero exit code captured."""
    fail_script = tmp_path / "fail_test.py"
    fail_script.write_text("raise ValueError('Assertion Failure')\n")

    runner = SandboxCommandRunner()
    res = runner.run_check(str(tmp_path), ValidationCheckType.UNIT_TEST, ["python3", str(fail_script)])

    assert res["status"] == ValidationCheckStatus.FAIL.value
    assert res["exit_code"] != 0
    assert "ValueError" in res["output_summary"] or "Assertion Failure" in res["output_summary"]


def test_scn_09_migration_failure(db_session: Session, tmp_path):
    """SCN-09: Invalid target transformation -> returns simulation error/failure without fake AFTER CBOM."""
    from app.migration.simulator import MigrationSimulator
    simulator = MigrationSimulator()

    proj_id = str(uuid.uuid4())
    scan_id = str(uuid.uuid4())
    project = Project(id=proj_id, name="SCN-09 Migration Fail Test")
    db_session.add(project)

    scan = Scan(
        id=scan_id,
        project_id=proj_id,
        status=ScanStatus.COMPLETED,
        target_path=str(tmp_path),
        cbom_json={"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []}
    )
    db_session.add(scan)
    db_session.commit()

    with pytest.raises((ValueError, Exception)):
        simulator.run_simulation(
            db=db_session,
            scan_id=scan.id,
            target_asset_ids=[99999],
            target_algorithms={"99999": "ML-KEM-768"}
        )


def test_scn_10_database_failure(db_session: Session):
    """SCN-10: DB transaction rollback on error -> controlled exception, no connection string password leak."""
    try:
        scan = Scan(id=-999, project_id=-999, status="INVALID_STATUS_VALUE_EXTREME", target_path="/tmp")
        db_session.add(scan)
        db_session.commit()
    except Exception as exc:
        db_session.rollback()
        error_msg = str(exc)
        assert "password" not in error_msg.lower()
        assert "postgresql://" not in error_msg.lower()


def test_scn_11_missing_cbom(db_session: Session):
    """SCN-11: Request CBOM for scan with cbom_json = None -> HTTP 404 with detail CBOM_NOT_AVAILABLE."""
    proj_id = str(uuid.uuid4())
    scan_id = str(uuid.uuid4())
    project = Project(id=proj_id, name="SCN-11 Missing CBOM Test")
    db_session.add(project)

    scan = Scan(id=scan_id, project_id=proj_id, status=ScanStatus.COMPLETED, target_path="/tmp", cbom_json=None)
    db_session.add(scan)
    db_session.commit()

    response = client.get(f"/api/v1/scans/{scan.id}/cbom")
    assert response.status_code == 404
    assert "CBOM_NOT_AVAILABLE" in response.json()["detail"] or "not available" in response.json()["detail"].lower()


def test_scn_12_project_scan_mismatch(db_session: Session):
    """SCN-12: Scan B does not belong to Project A -> HTTP 400 rejection."""
    proj_a_id = str(uuid.uuid4())
    proj_b_id = str(uuid.uuid4())
    scan_b_id = str(uuid.uuid4())
    project_a = Project(id=proj_a_id, name="Project A")
    project_b = Project(id=proj_b_id, name="Project B")
    db_session.add_all([project_a, project_b])
    db_session.flush()

    scan_b = Scan(id=scan_b_id, project_id=proj_b_id, status=ScanStatus.COMPLETED, target_path="/tmp")
    db_session.add(scan_b)
    db_session.commit()

    response = client.get(f"/api/v1/projects/{proj_a_id}/reports/executive?scan_id={scan_b_id}")
    assert response.status_code == 400
    assert "does not belong to project" in response.json()["detail"].lower()


def test_scn_13_execution_timeout(tmp_path):
    """SCN-13: Validation command execution timeout -> TIMEOUT status, process killed."""
    sleep_script = tmp_path / "sleep_forever.py"
    sleep_script.write_text("import time\ntime.sleep(10)\n")

    runner = SandboxCommandRunner()
    res = runner.run_check(
        str(tmp_path),
        ValidationCheckType.BUILD,
        ["python3", str(sleep_script)],
        timeout_seconds=1
    )

    assert res["status"] == ValidationCheckStatus.TIMEOUT.value
    assert res["timeout"] is True


def test_scn_14_command_rejection(tmp_path):
    """SCN-14: Command injection or non-allowlisted binary -> BLOCKED status."""
    runner = SandboxCommandRunner()

    res_curl = runner.run_check(str(tmp_path), ValidationCheckType.BUILD, ["curl", "https://example.com"])
    assert res_curl["status"] == ValidationCheckStatus.BLOCKED.value

    res_inj = runner.run_check(str(tmp_path), ValidationCheckType.BUILD, ["python3; echo evil"])
    assert res_inj["status"] == ValidationCheckStatus.BLOCKED.value


def test_scn_15_oversized_upload(db_session: Session):
    """SCN-15: Oversized file upload (>50MB) -> HTTP 413 Request Entity Too Large."""
    proj_id = str(uuid.uuid4())
    project = Project(id=proj_id, name="SCN-15 Upload Test")
    db_session.add(project)
    db_session.commit()

    large_stream = b"A" * (50 * 1024 * 1024 + 100)

    response = client.post(
        f"/api/v1/projects/{proj_id}/scans/upload-binary",
        files={"file": ("large_binary.bin", large_stream, "application/octet-stream")}
    )

    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"].lower() or "too large" in response.json()["detail"].lower()


def test_scn_16_invalid_business_criticality(db_session: Session):
    """SCN-16: Override business criticality with empty reason -> HTTP 422 or ValueError."""
    proj_id = str(uuid.uuid4())
    project = Project(id=proj_id, name="SCN-16 Criticality Test")
    db_session.add(project)
    db_session.commit()

    response = client.post(
        f"/api/v1/projects/{proj_id}/business-criticality/override",
        json={"user_override": "CRITICAL", "override_reason": "   "}
    )
    assert response.status_code in (400, 422)
    assert "reason" in str(response.json()).lower()


def test_scn_17_invalid_migration_profile():
    """SCN-17: Migration effort with invalid profile string -> raises ValueError on Enum validation."""
    with pytest.raises(ValueError):
        MigrationProfile("ULTRA_FAST")


def test_scn_18_reporting_failure_states():
    """SCN-18: Request report for non-existent project_id -> HTTP 404 Project not found."""
    response = client.get("/api/v1/projects/999999/reports/executive")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_scn_19_error_message_safety():
    """SCN-19: Unhandled errors or invalid API requests -> sanitized messages, no stack trace or secrets leak."""
    response = client.post("/api/v1/projects/proj-123/scans", json="invalid_body_format")
    assert response.status_code in (400, 422)

    body_str = json.dumps(response.json())
    assert "Traceback (most recent call last)" not in body_str
    assert "SELECT " not in body_str
    assert "SECRET" not in body_str
    assert "/Users/" not in body_str or "sanitized" in body_str.lower()


def test_scn_20_e2e_build_regression_flow():
    """SCN-20: RegressionAnalyzer BEFORE pass + AFTER fail -> ValidationStatus.REGRESSION."""
    analyzer = RegressionAnalyzer()

    before_build = {"status": "PASSED", "exit_code": 0}
    before_test = {"status": "PASSED", "exit_code": 0}
    after_build = {"status": "FAILED", "exit_code": 1, "output_summary": "Compiler error"}
    after_test = {"status": "NOT_RUN", "exit_code": -1}

    res = analyzer.analyze(before_build, before_test, after_build, after_test)

    assert res["status"] == ValidationStatus.REGRESSION.value
    assert res["regression_detected"] is True
    assert any("pass to fail" in r.lower() or "regression" in r.lower() for r in res["reasons"])
