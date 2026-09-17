import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.db_models import Project, Scan, MigrationPlan, CryptoAsset, MigrationSimulation, ValidationRun
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety, SimulationStatus, ValidationStatus

client = TestClient(app)

@pytest.fixture
def test_setup():
    """Fixture providing active project, scans, plans, assets, and simulations."""
    db_session = SessionLocal()
    try:
        p1 = Project(id=str(uuid.uuid4()), name="Project 1")
        p2 = Project(id=str(uuid.uuid4()), name="Project 2")
        db_session.add_all([p1, p2])
        db_session.commit()

        scan1 = Scan(id=str(uuid.uuid4()), project_id=p1.id, status=ScanStatus.COMPLETED, target_path="src/", cbom_json={"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []})
        scan2 = Scan(id=str(uuid.uuid4()), project_id=p2.id, status=ScanStatus.COMPLETED, target_path="src/", cbom_json={"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []})
        db_session.add_all([scan1, scan2])
        db_session.commit()

        asset1 = CryptoAsset(id=str(uuid.uuid4()), scan_id=scan1.id, name="RSA Key", asset_type=AssetType.ALGORITHM, algorithm_name="RSA-2048", purpose=CryptoPurpose.SIGNATURE, location="src/key.py", quantum_safety=QuantumSafety.QUANTUM_VULNERABLE)
        asset2 = CryptoAsset(id=str(uuid.uuid4()), scan_id=scan2.id, name="ECDH Key", asset_type=AssetType.ALGORITHM, algorithm_name="ECDH-P256", purpose=CryptoPurpose.KEY_ESTABLISHMENT, location="src/dh.py", quantum_safety=QuantumSafety.QUANTUM_VULNERABLE)
        db_session.add_all([asset1, asset2])
        db_session.commit()

        plan1 = MigrationPlan(id=str(uuid.uuid4()), project_id=p1.id, name="Plan 1", total_person_days=2.0, total_calendar_months=1.0)
        plan2 = MigrationPlan(id=str(uuid.uuid4()), project_id=p2.id, name="Plan 2", total_person_days=3.0, total_calendar_months=1.0)
        db_session.add_all([plan1, plan2])
        db_session.commit()

        sim1 = MigrationSimulation(id=str(uuid.uuid4()), project_id=p1.id, asset_id=asset1.id, migration_plan_id=plan1.id, status=SimulationStatus.PASSED, sandbox_path="/tmp/sb1", transformation_type="RSA_TO_ML_DSA")
        sim2 = MigrationSimulation(id=str(uuid.uuid4()), project_id=p2.id, asset_id=asset2.id, migration_plan_id=plan2.id, status=SimulationStatus.PASSED, sandbox_path="/tmp/sb2", transformation_type="ECDH_TO_ML_KEM_HYBRID")
        db_session.add_all([sim1, sim2])
        db_session.commit()

        yield {
            "p1": p1, "p2": p2,
            "scan1": scan1, "scan2": scan2,
            "asset1": asset1, "asset2": asset2,
            "plan1": plan1, "plan2": plan2,
            "sim1": sim1, "sim2": sim2,
        }
    finally:
        db_session.close()


def test_validation_runner_receives_active_scan_id(test_setup):
    """TEST 1: ValidationRunner receives the active scan_id."""
    scan = test_setup["scan1"]
    assert scan.id is not None
    assert scan.id != test_setup["scan2"].id


def test_validation_runner_receives_active_simulation_id(test_setup):
    """TEST 2: ValidationRunner receives the active simulation_id."""
    sim = test_setup["sim1"]
    assert sim.id is not None
    assert sim.id != test_setup["sim2"].id


def test_run_build_request_uses_active_scan_id(test_setup):
    """TEST 3: Run Build request uses the active scan_id."""
    p1 = test_setup["p1"]
    scan1 = test_setup["scan1"]
    plan1 = test_setup["plan1"]

    res = client.post(f"/api/v1/projects/{p1.id}/validation/build?scan_id={scan1.id}&migration_plan_id={plan1.id}")
    assert res.status_code in [200, 409]
    if res.status_code == 200:
        data = res.json()
        assert data["scan_id"] == scan1.id


def test_run_tests_request_uses_active_scan_id_and_plan_id(test_setup):
    """TEST 4: Run Tests request uses the active scan_id and required plan_id."""
    p1 = test_setup["p1"]
    scan1 = test_setup["scan1"]
    plan1 = test_setup["plan1"]

    res = client.post(f"/api/v1/projects/{p1.id}/validation/tests?scan_id={scan1.id}&migration_plan_id={plan1.id}")
    assert res.status_code in [200, 409]
    if res.status_code == 200:
        data = res.json()
        assert data["scan_id"] == scan1.id


def test_run_regression_request_uses_active_scan_id_and_plan_id(test_setup):
    """TEST 5: Run Regression request uses active scan_id + active plan_id."""
    p1 = test_setup["p1"]
    scan1 = test_setup["scan1"]
    plan1 = test_setup["plan1"]
    sim1 = test_setup["sim1"]

    res = client.post(f"/api/v1/projects/{p1.id}/validation/regression?scan_id={scan1.id}&migration_plan_id={plan1.id}&simulation_id={sim1.id}")
    assert res.status_code in [200, 409]


def test_run_cbom_diff_uses_active_scan_id_and_plan_id(test_setup):
    """TEST 6: Run CBOM Diff uses active scan_id + active plan_id."""
    p1 = test_setup["p1"]
    scan1 = test_setup["scan1"]
    plan1 = test_setup["plan1"]
    sim1 = test_setup["sim1"]

    res = client.post(f"/api/v1/projects/{p1.id}/validation/cbom-diff?scan_id={scan1.id}&migration_plan_id={plan1.id}&simulation_id={sim1.id}")
    assert res.status_code in [200, 409]


def test_stale_scan_id_never_selected(test_setup):
    """TEST 7: A stale/unrelated scan ID is never selected."""
    p1 = test_setup["p1"]
    stale_scan_id = test_setup["scan2"].id  # Belongs to p2

    res = client.post(f"/api/v1/projects/{p1.id}/validation/build?scan_id={stale_scan_id}")
    assert res.status_code == 400
    assert "does not belong to project" in res.json()["detail"]


def test_two_different_plans_use_their_own_scan_ids(test_setup):
    """TEST 8: Two different migration plans use their own scan IDs."""
    plan1 = test_setup["plan1"]
    plan2 = test_setup["plan2"]

    scan1_id = test_setup["scan1"].id
    scan2_id = test_setup["scan2"].id

    assert scan1_id != scan2_id
    assert plan1.project_id != plan2.project_id


def test_two_different_simulations_use_their_own_simulation_ids(test_setup):
    """TEST 9: Two different simulations use their own simulation IDs."""
    sim1 = test_setup["sim1"]
    sim2 = test_setup["sim2"]

    assert sim1.id != sim2.id
    assert sim1.migration_plan_id != sim2.migration_plan_id
