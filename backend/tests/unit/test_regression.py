import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.validation.regression import RegressionAnalyzer, RegressionValidationService
from app.models.enums import ValidationStatus
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

# --- 1. REGRESSION ANALYZER UNIT TESTS ---

def test_regression_analyzer_no_regression():
    analyzer = RegressionAnalyzer()
    before_b = {"status": "PASSED", "exit_code": 0}
    before_t = {"status": "PASSED", "exit_code": 0, "tests_passed": 10, "tests_failed": 0}
    after_b = {"status": "PASSED", "exit_code": 0}
    after_t = {"status": "PASSED", "exit_code": 0, "tests_passed": 10, "tests_failed": 0}

    res = analyzer.analyze(before_b, before_t, after_b, after_t)
    assert res["status"] == "NO_REGRESSION"
    assert res["regression_detected"] is False

def test_regression_analyzer_build_pass_to_fail():
    analyzer = RegressionAnalyzer()
    before_b = {"status": "PASSED", "exit_code": 0}
    before_t = {"status": "PASSED", "exit_code": 0}
    after_b = {"status": "FAILED", "exit_code": 1}
    after_t = {"status": "NOT_RUN", "exit_code": -1}

    res = analyzer.analyze(before_b, before_t, after_b, after_t)
    assert res["status"] == "REGRESSION"
    assert res["regression_detected"] is True
    assert any("Build changed from PASS to FAIL" in r for r in res["reasons"])

def test_regression_analyzer_build_pass_to_timeout():
    analyzer = RegressionAnalyzer()
    before_b = {"status": "PASSED", "exit_code": 0}
    before_t = {"status": "PASSED", "exit_code": 0}
    after_b = {"status": "TIMEOUT", "exit_code": 124}
    after_t = {"status": "NOT_RUN", "exit_code": -1}

    res = analyzer.analyze(before_b, before_t, after_b, after_t)
    assert res["status"] == "REGRESSION"
    assert res["regression_detected"] is True
    assert any("TIMEOUT" in r for r in res["reasons"])

def test_regression_analyzer_test_pass_to_fail():
    analyzer = RegressionAnalyzer()
    before_b = {"status": "PASSED", "exit_code": 0}
    before_t = {"status": "PASSED", "exit_code": 0}
    after_b = {"status": "PASSED", "exit_code": 0}
    after_t = {"status": "FAILED", "exit_code": 1}

    res = analyzer.analyze(before_b, before_t, after_b, after_t)
    assert res["status"] == "REGRESSION"
    assert res["regression_detected"] is True
    assert any("Unit tests changed from PASS to FAIL" in r for r in res["reasons"])

def test_regression_analyzer_test_pass_to_timeout():
    analyzer = RegressionAnalyzer()
    before_b = {"status": "PASSED", "exit_code": 0}
    before_t = {"status": "PASSED", "exit_code": 0}
    after_b = {"status": "PASSED", "exit_code": 0}
    after_t = {"status": "TIMEOUT", "exit_code": 124}

    res = analyzer.analyze(before_b, before_t, after_b, after_t)
    assert res["status"] == "REGRESSION"
    assert res["regression_detected"] is True

def test_regression_analyzer_test_fail_to_pass_improved():
    analyzer = RegressionAnalyzer()
    before_b = {"status": "PASSED", "exit_code": 0}
    before_t = {"status": "FAILED", "exit_code": 1}
    after_b = {"status": "PASSED", "exit_code": 0}
    after_t = {"status": "PASSED", "exit_code": 0}

    res = analyzer.analyze(before_b, before_t, after_b, after_t)
    assert res["status"] == "IMPROVED"
    assert res["regression_detected"] is False

def test_regression_analyzer_baseline_failed():
    analyzer = RegressionAnalyzer()
    before_b = {"status": "FAILED", "exit_code": 1}
    before_t = {"status": "FAILED", "exit_code": 1}
    after_b = {"status": "FAILED", "exit_code": 1}
    after_t = {"status": "FAILED", "exit_code": 1}

    res = analyzer.analyze(before_b, before_t, after_b, after_t)
    assert res["status"] == "BASELINE_FAILED"
    assert res["regression_detected"] is False

def test_regression_analyzer_migration_failed():
    analyzer = RegressionAnalyzer()
    before_b = {"status": "PASSED", "exit_code": 0}
    before_t = {"status": "PASSED", "exit_code": 0}

    res = analyzer.analyze(before_b, before_t, {}, {}, migration_result={"status": "FAILED", "error": "AST transformation syntax error"})
    assert res["status"] == "MIGRATION_FAILED"
    assert res["regression_detected"] is False
    assert any("Migration failed" in r for r in res["reasons"])

def test_regression_analyzer_count_degradation():
    analyzer = RegressionAnalyzer()
    before_b = {"status": "PASSED", "exit_code": 0}
    before_t = {"status": "PASSED", "exit_code": 0, "tests_passed": 20, "tests_failed": 0}
    after_b = {"status": "PASSED", "exit_code": 0}
    after_t = {"status": "PASSED", "exit_code": 0, "tests_passed": 18, "tests_failed": 2}

    res = analyzer.analyze(before_b, before_t, after_b, after_t)
    assert res["status"] == "REGRESSION"
    assert res["regression_detected"] is True
    assert any("decreased from 20 to 18" in r for r in res["reasons"])

def test_regression_analyzer_unconfigured():
    analyzer = RegressionAnalyzer()
    before_b = {"status": "NOT_CONFIGURED"}
    before_t = {"status": "NOT_CONFIGURED"}
    after_b = {"status": "NOT_CONFIGURED"}
    after_t = {"status": "NOT_CONFIGURED"}

    res = analyzer.analyze(before_b, before_t, after_b, after_t)
    assert res["status"] == "NOT_CONFIGURED"
    assert res["regression_detected"] is False

# --- 2. API CONTRACT & OWNERSHIP TESTS ---

def test_api_regression_validation_non_existent_project_404(client):
    response = client.post("/api/v1/projects/non-existent-proj-8888/validation/regression")
    assert response.status_code == 404

def test_api_regression_validation_mismatched_scan_400(client, db_session):
    p1 = Project(id="p1_reg", name="p1")
    p2 = Project(id="p2_reg", name="p2")
    scan_p2 = Scan(id="scan_p2_reg", project_id="p2_reg", target_path="/tmp")
    db_session.add_all([p1, p2, scan_p2])
    db_session.commit()

    response = client.post("/api/v1/projects/p1_reg/validation/regression?scan_id=scan_p2_reg")
    assert response.status_code == 400

def test_api_regression_validation_generic_exception_500(client, db_session, monkeypatch):
    p = Project(id="p_gen_err", name="p_err")
    s = Scan(id="scan_gen_err", project_id="p_gen_err", target_path="/tmp")
    db_session.add_all([p, s])
    db_session.commit()

    def mock_run_pipeline(*args, **kwargs):
        raise RuntimeError("Simulated unexpected engine exception")

    monkeypatch.setattr(
        "app.validation.regression.RegressionValidationService.run_full_regression_pipeline",
        mock_run_pipeline
    )

    response = client.post("/api/v1/projects/p_gen_err/validation/regression?scan_id=scan_gen_err")
    assert response.status_code == 500
    assert response.json() == {
        "detail": "Regression validation execution failed.",
        "error_code": "REGRESSION_EXECUTION_ERROR"
    }

# --- 3. END-TO-END FIXTURE VALIDATION TESTS ---

def test_e2e_regression_pipeline_no_regression(client, db_session):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a passing Python project
        with open(os.path.join(tmpdir, "app.py"), "w") as f:
            f.write("def add(a, b):\n    return a + b\n")
        with open(os.path.join(tmpdir, "test_app.py"), "w") as f:
            f.write("import unittest\nfrom app import add\nclass TestApp(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(1, 2), 3)\n")

        p = Project(id="proj_e2e_pass", name="E2E Pass Proj")
        s = Scan(id="scan_e2e_pass", project_id="proj_e2e_pass", target_path=tmpdir)
        db_session.add_all([p, s])
        db_session.commit()

        response = client.post("/api/v1/projects/proj_e2e_pass/validation/regression?scan_id=scan_e2e_pass")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == "proj_e2e_pass"
        assert data["check_type"] == "REGRESSION"
        assert data["status"] == "NO_REGRESSION"
        assert data["regression_detected"] is False
        assert data["before"]["tests"]["status"] in ["PASS", "PASSED"]
        assert data["after"]["tests"]["status"] in ["PASS", "PASSED"]
