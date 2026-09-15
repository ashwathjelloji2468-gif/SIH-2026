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
from app.validation.detector import TestDetector, parse_test_counts
from app.validation.runner import SandboxCommandRunner
from app.models.enums import ValidationCheckStatus, ValidationCheckType, ValidationStatus
from app.models.db_models import Project, Scan, ValidationRun

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
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)

@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

# --- 1. TEST FRAMEWORK DETECTION TESTS ---

def test_detector_node_npm_script():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('{"name": "test-pkg", "scripts": {"test": "jest"}}')
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "CONFIGURED"
        assert "Node.js (npm)" in cfg["framework"]
        assert cfg["commands"] == [["npm", "test"]]

def test_detector_node_yarn_lock():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('{"name": "test-pkg", "scripts": {"test": "vitest"}}')
        open(os.path.join(tmpdir, "yarn.lock"), "w").close()
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "CONFIGURED"
        assert "Node.js (yarn)" in cfg["framework"]
        assert cfg["commands"] == [["yarn", "test"]]

def test_detector_node_pnpm_lock():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('{"name": "test-pkg", "scripts": {"test": "mocha"}}')
        open(os.path.join(tmpdir, "pnpm-lock.yaml"), "w").close()
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "CONFIGURED"
        assert "Node.js (pnpm)" in cfg["framework"]
        assert cfg["commands"] == [["pnpm", "test"]]

def test_detector_node_bun_lock():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('{"name": "test-pkg", "scripts": {"test": "bun test"}}')
        open(os.path.join(tmpdir, "bun.lock"), "w").close()
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "CONFIGURED"
        assert "Node.js (bun)" in cfg["framework"]
        assert cfg["commands"] == [["bun", "test"]]

def test_detector_node_no_test_script():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('{"name": "test-pkg", "scripts": {"build": "tsc"}}')
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "NOT_CONFIGURED"
        assert "Node.js" in cfg["framework"]
        assert cfg["commands"] == []

def test_detector_python_pytest():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "pytest.ini"), "w").close()
        open(os.path.join(tmpdir, "test_main.py"), "w").close()
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "CONFIGURED"
        assert cfg["framework"] == "Python (pytest)"
        assert cfg["commands"] == [["python3", "-m", "pytest"]]

def test_detector_python_unittest():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "app.py"), "w").close()
        open(os.path.join(tmpdir, "test_app.py"), "w").close()
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "CONFIGURED"
        assert "Python" in cfg["framework"]
        assert len(cfg["commands"]) == 1

def test_detector_python_no_tests():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "requirements.txt"), "w").close()
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "NOT_CONFIGURED"
        assert cfg["framework"] == "Python"
        assert cfg["commands"] == []

def test_detector_java_maven():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "pom.xml"), "w").close()
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "CONFIGURED"
        assert cfg["framework"] == "Java (Maven)"
        assert cfg["commands"] == [["mvn", "test"]]

def test_detector_java_gradle_wrapper():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "gradlew"), "w").close()
        open(os.path.join(tmpdir, "build.gradle"), "w").close()
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "CONFIGURED"
        assert cfg["framework"] == "Java (Gradle)"
        assert cfg["commands"] == [["./gradlew", "test"]]

def test_detector_go():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "go.mod"), "w").close()
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "CONFIGURED"
        assert cfg["framework"] == "Go"
        assert cfg["commands"] == [["go", "test", "./..."]]

def test_detector_rust():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "Cargo.toml"), "w").close()
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "CONFIGURED"
        assert cfg["framework"] == "Rust"
        assert cfg["commands"] == [["cargo", "test"]]

def test_detector_cmake_ctest():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "CMakeLists.txt"), "w") as f:
            f.write("cmake_minimum_required(VERSION 3.10)\nenable_testing()\nadd_test(NAME t1 COMMAND app)")
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "CONFIGURED"
        assert cfg["framework"] == "C/C++ (CTest)"
        assert cfg["commands"] == [["ctest"]]

def test_detector_unsupported():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "README.txt"), "w").close()
        
        cfg = detector.detect_test_config(tmpdir)
        assert cfg["status"] == "NOT_SUPPORTED"
        assert cfg["framework"] == "Unknown"

# --- 2. TEST COUNT PARSER TESTS ---

def test_parse_test_counts_pytest():
    log_sample = "================ 23 passed, 2 failed, 1 skipped in 1.45s ================"
    counts = parse_test_counts(log_sample)
    assert counts["total"] == 26
    assert counts["passed"] == 23
    assert counts["failed"] == 2
    assert counts["skipped"] == 1

def test_parse_test_counts_unittest_ok():
    log_sample = "Ran 12 tests in 0.004s\n\nOK"
    counts = parse_test_counts(log_sample)
    assert counts["total"] == 12
    assert counts["passed"] == 12
    assert counts["failed"] == 0

def test_parse_test_counts_jest():
    log_sample = "Tests:       1 failed, 8 passed, 9 total"
    counts = parse_test_counts(log_sample)
    assert counts["total"] == 9
    assert counts["passed"] == 8
    assert counts["failed"] == 1

def test_parse_test_counts_cargo():
    log_sample = "test result: ok. 5 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out"
    counts = parse_test_counts(log_sample)
    assert counts["total"] == 6
    assert counts["passed"] == 5
    assert counts["failed"] == 0
    assert counts["skipped"] == 1

def test_parse_test_counts_unrecognized_returns_none():
    log_sample = "Build finished successfully."
    counts = parse_test_counts(log_sample)
    assert counts["total"] is None
    assert counts["passed"] is None

# --- 3. EXECUTION & PROCESS FIXTURE TESTS ---

def test_runner_passing_test_fixture():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_sample.py")
        with open(test_file, "w") as f:
            f.write("import unittest\nclass TestSimple(unittest.TestCase):\n    def test_ok(self):\n        self.assertEqual(1+1, 2)\n")
        
        res = runner.run_check(tmpdir, ValidationCheckType.UNIT_TEST, ["python3", "-m", "unittest", "discover"])
        assert res["status"] == ValidationCheckStatus.PASS.value
        assert res["exit_code"] == 0

def test_runner_failing_test_fixture():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_fail.py")
        with open(test_file, "w") as f:
            f.write("import unittest\nclass TestFail(unittest.TestCase):\n    def test_err(self):\n        self.assertEqual(1, 2)\n")
        
        res = runner.run_check(tmpdir, ValidationCheckType.UNIT_TEST, ["python3", "-m", "unittest", "discover"])
        assert res["status"] == ValidationCheckStatus.FAIL.value
        assert res["exit_code"] != 0

def test_runner_test_timeout_fixture():
    runner = SandboxCommandRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        res = runner.run_check(tmpdir, ValidationCheckType.UNIT_TEST, ["python3", "-c", "__import__('time').sleep(5)"], timeout_seconds=1)
        assert res["status"] == ValidationCheckStatus.TIMEOUT.value
        assert res["timeout"] is True

# --- 4. API CONTRACT & OWNERSHIP TESTS ---

def test_api_test_validation_non_existent_project_returns_404(client):
    response = client.post("/api/v1/projects/non-existent-project-7777/validation/tests")
    assert response.status_code == 404

def test_api_test_validation_mismatched_scan_returns_400(client, db_session):
    p1 = Project(id="p1_test", name="p1")
    p2 = Project(id="p2_test", name="p2")
    scan_p2 = Scan(id="scan_p2", project_id="p2_test", target_path="/tmp")
    db_session.add_all([p1, p2, scan_p2])
    db_session.commit()

    response = client.post("/api/v1/projects/p1_test/validation/tests?scan_id=scan_p2")
    assert response.status_code == 400
    assert "does not belong" in response.json()["detail"]

def test_api_test_validation_success(client, db_session):
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "test_api.py"), "w") as f:
            f.write("import unittest\nclass TestApi(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n")

        p = Project(id="proj_api_test", name="API Test Proj")
        s = Scan(id="scan_api_test", project_id="proj_api_test", target_path=tmpdir)
        db_session.add_all([p, s])
        db_session.commit()

        response = client.post(f"/api/v1/projects/proj_api_test/validation/tests?scan_id=scan_api_test")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == "proj_api_test"
        assert data["scan_id"] == "scan_api_test"
        assert data["check_type"] == "UNIT_TEST"
        assert data["status"] in ["PASS", "PASSED"]
        assert data["exit_code"] == 0
        assert data["unit_tests_passed"] is True
