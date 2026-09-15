import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.db_models import Project, Scan, ValidationRun
from app.models.enums import ValidationCheckType, ValidationCheckStatus, ValidationStatus
from app.validation.detector import BuildDetector
from app.validation.runner import SandboxCommandRunner, mask_secrets, truncate_logs

# In-memory SQLite Test Database Setup
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


# --- 1. BUILD SYSTEM DETECTION TESTS ---

def test_detector_node_npm_build_script():
    detector = BuildDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('{"name": "test", "scripts": {"build": "vite build"}}')

        res = detector.detect_build_config(tmpdir)
        assert res["status"] == "CONFIGURED"
        assert "npm" in res["framework"]
        assert res["commands"] == [["npm", "run", "build"]]

def test_detector_node_yarn_lock():
    detector = BuildDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('{"name": "test", "scripts": {"build": "webpack"}}')
        with open(os.path.join(tmpdir, "yarn.lock"), "w") as f:
            f.write("# yarn lock")

        res = detector.detect_build_config(tmpdir)
        assert res["status"] == "CONFIGURED"
        assert "yarn" in res["framework"]
        assert res["commands"] == [["yarn", "build"]]

def test_detector_node_pnpm_lock():
    detector = BuildDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('{"name": "test", "scripts": {"build": "tsc"}}')
        with open(os.path.join(tmpdir, "pnpm-lock.yaml"), "w") as f:
            f.write("lockfileVersion: 5.4")

        res = detector.detect_build_config(tmpdir)
        assert res["status"] == "CONFIGURED"
        assert "pnpm" in res["framework"]
        assert res["commands"] == [["pnpm", "build"]]

def test_detector_node_bun_lock():
    detector = BuildDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('{"name": "test", "scripts": {"build": "bun build ./src/index.ts"}}')
        with open(os.path.join(tmpdir, "bun.lockb"), "w") as f:
            f.write("bun lock")

        res = detector.detect_build_config(tmpdir)
        assert res["status"] == "CONFIGURED"
        assert "bun" in res["framework"]
        assert res["commands"] == [["bun", "run", "build"]]

def test_detector_node_no_build_script_returns_not_configured():
    detector = BuildDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('{"name": "test", "scripts": {"test": "jest"}}')

        res = detector.detect_build_config(tmpdir)
        assert res["status"] == "NOT_CONFIGURED"
        assert res["commands"] == []

def test_detector_java_maven():
    detector = BuildDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pom.xml"), "w") as f:
            f.write("<project></project>")

        res = detector.detect_build_config(tmpdir)
        assert res["status"] == "CONFIGURED"
        assert "Maven" in res["framework"]
        assert res["commands"] == [["mvn", "compile"]]

def test_detector_java_gradle():
    detector = BuildDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "build.gradle"), "w") as f:
            f.write("// gradle build")

        res = detector.detect_build_config(tmpdir)
        assert res["status"] == "CONFIGURED"
        assert "Gradle" in res["framework"]
        assert res["commands"] == [["gradle", "classes"]]

def test_detector_c_cpp_cmake_2_stage():
    detector = BuildDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "CMakeLists.txt"), "w") as f:
            f.write("cmake_minimum_required(VERSION 3.10)")

        res = detector.detect_build_config(tmpdir)
        assert res["status"] == "CONFIGURED"
        assert "CMake" in res["framework"]
        # 2-stage build: configure then compile
        assert res["commands"] == [["cmake", "-B", "build"], ["cmake", "--build", "build"]]

def test_detector_c_cpp_make():
    detector = BuildDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "Makefile"), "w") as f:
            f.write("all:\n\techo build")

        res = detector.detect_build_config(tmpdir)
        assert res["status"] == "CONFIGURED"
        assert "Make" in res["framework"]
        assert res["commands"] == [["make"]]

def test_detector_python_returns_not_configured():
    detector = BuildDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("[build-system]\nrequires = ['setuptools']")

        res = detector.detect_build_config(tmpdir)
        assert res["status"] == "NOT_CONFIGURED"
        assert "Python" in res["framework"]

def test_detector_unsupported_returns_not_supported():
    detector = BuildDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        res = detector.detect_build_config(tmpdir)
        assert res["status"] == "NOT_SUPPORTED"
        assert res["framework"] == "Unknown"


# --- 2. COMMAND ALLOWLIST & SECURITY TESTS ---

def test_runner_rejects_forbidden_executable():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        res = runner.run_check(tmpdir, ValidationCheckType.BUILD, ["curl", "https://example.com"])
        assert res["status"] == ValidationCheckStatus.BLOCKED.value
        assert "explicitly forbidden" in res["output_summary"] or "blocked" in res["output_summary"].lower()

def test_runner_rejects_non_allowlisted_executable():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        res = runner.run_check(tmpdir, ValidationCheckType.BUILD, ["custom_binary", "--flag"])
        assert res["status"] == ValidationCheckStatus.BLOCKED.value
        assert "not in security allowlist" in res["output_summary"]

def test_runner_rejects_dangerous_shell_characters():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        res = runner.run_check(tmpdir, ValidationCheckType.BUILD, ["python3", "-c", "import sys; print('test'); import os; os.system('ls || echo bad')"])
        # Contains || shell metacharacter
        assert res["status"] == ValidationCheckStatus.BLOCKED.value
        assert "illegal shell meta-characters" in res["output_summary"] or "Dangerous character" in str(res["evidence"])


# --- 3. PROCESS EXECUTION, TIMEOUT & LOG TESTS ---

def test_runner_successful_execution_returns_pass():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        res = runner.run_check(tmpdir, ValidationCheckType.BUILD, ["python3", "-c", "print('Build Success')"])
        assert res["status"] == ValidationCheckStatus.PASS.value
        assert res["exit_code"] == 0
        assert res["timeout"] is False
        assert "Build Success" in res["logs"]

def test_runner_failing_execution_returns_fail():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        res = runner.run_check(tmpdir, ValidationCheckType.BUILD, ["python3", "-c", "raise RuntimeError('Build Error')"])
        assert res["status"] == ValidationCheckStatus.FAIL.value
        assert res["exit_code"] != 0
        assert res["timeout"] is False

def test_runner_timeout_terminates_process_tree_returns_timeout():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Sleep for 5 seconds with a 1 second timeout
        res = runner.run_check(tmpdir, ValidationCheckType.BUILD, ["python3", "-c", "__import__('time').sleep(5)"], timeout_seconds=1)
        assert res["status"] == ValidationCheckStatus.TIMEOUT.value
        assert res["exit_code"] == 124
        assert res["timeout"] is True
        assert res["status"] != ValidationCheckStatus.PASS.value

def test_mask_secrets_redacts_credentials():
    raw_log = (
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----\n"
        "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
        "password='SuperSecretPassword123'\n"
    )
    masked = mask_secrets(raw_log)
    assert "-----BEGIN RSA PRIVATE KEY-----" not in masked
    assert "[MASKED_PRIVATE_KEY]" in masked
    assert "SuperSecretPassword123" not in masked

def test_truncate_logs_enforces_max_size():
    huge_log = "A" * 60000
    truncated = truncate_logs(huge_log, max_bytes=50000)
    assert len(truncated) < 60000
    assert "[LOG OUTPUT TRUNCATED — MAXIMUM SIZE REACHED]" in truncated


# --- 4. API CONTRACT & OWNERSHIP VALIDATION TESTS ---

def test_api_build_validation_non_existent_project_returns_404(client):
    response = client.post("/api/v1/projects/non-existent-project-9999/validation/build")
    assert response.status_code == 404

def test_api_build_validation_mismatched_scan_returns_400(client, db_session):
    p1 = Project(name="p1")
    p2 = Project(name="p2")
    db_session.add_all([p1, p2])
    db_session.commit()

    scan_p2 = Scan(project_id=p2.id, target_path="/tmp")
    db_session.add(scan_p2)
    db_session.commit()

    # Pass scan_p2 ID to project p1
    response = client.post(f"/api/v1/projects/{p1.id}/validation/build?scan_id={scan_p2.id}")
    assert response.status_code == 400
    assert "does not belong to project" in response.json()["detail"]

def test_api_build_validation_missing_source_path_returns_409(client, db_session):
    proj = Project(name="missing-source-proj")
    db_session.add(proj)
    db_session.commit()

    scan = Scan(project_id=proj.id, target_path="/nonexistent/directory/path/for/test")
    db_session.add(scan)
    db_session.commit()

    response = client.post(f"/api/v1/projects/{proj.id}/validation/build")
    assert response.status_code == 409
    assert "does not exist on disk" in response.json()["detail"]

def test_api_build_validation_success(client, db_session):
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('''{"name": "real-app", "scripts": {"build": "python3 -c \\"print('Built Successfully')\\""}}''')

        proj = Project(name="valid-node-proj")
        db_session.add(proj)
        db_session.commit()

        scan = Scan(project_id=proj.id, target_path=tmpdir)
        db_session.add(scan)
        db_session.commit()

        response = client.post(f"/api/v1/projects/{proj.id}/validation/build")
        assert response.status_code == 200
        data = response.json()

        assert data["project_id"] == proj.id
        assert data["scan_id"] == scan.id
        assert data["check_type"] == "BUILD"
        assert data["status"] == "PASSED"
        assert data["build_passed"] is True
        assert data["exit_code"] == 0
        assert data["timeout"] is False
        assert "Built Successfully" in data["logs"]
