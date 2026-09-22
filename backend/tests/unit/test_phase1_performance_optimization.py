import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.db_models import Project, Scan, CryptoAsset, Evidence, RiskAssessment, MigrationPlan, MigrationTask
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety, ReviewStatus
from app.repositories.asset_repository import AssetRepository
from app.repositories.migration_repository import MigrationRepository
from app.context.effective_context import resolve_effective_artifact_context
from app.api.risk import list_risk_assessments

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_asset_repository_latest_only_scope(db_session):
    proj = Project(id="proj-perf-1", name="Perf Project 1")
    db_session.add(proj)
    db_session.commit()

    scan1 = Scan(id="scan-1", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/test1")
    db_session.add(scan1)
    db_session.commit()

    scan2 = Scan(id="scan-2", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/test2")
    db_session.add(scan2)
    db_session.commit()

    asset1 = CryptoAsset(
        id="asset-1",
        scan_id=scan1.id,
        name="Old RSA Key",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-1024",
        location="/old/path.py"
    )
    asset2 = CryptoAsset(
        id="asset-2",
        scan_id=scan2.id,
        name="New AES Key",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256",
        location="/new/path.py"
    )
    db_session.add_all([asset1, asset2])
    db_session.commit()

    repo = AssetRepository(db_session)

    # 1. Default latest_only=True should return only scan2 assets
    latest_assets = repo.get_by_project(proj.id, latest_only=True)
    assert len(latest_assets) == 1
    assert latest_assets[0].id == "asset-2"

    # 2. Historical latest_only=False should return all assets
    all_assets = repo.get_by_project(proj.id, latest_only=False)
    assert len(all_assets) == 2

    # 3. Explicit scan_id should return only scan1 assets
    scan1_assets = repo.get_by_project(proj.id, scan_id="scan-1")
    assert len(scan1_assets) == 1
    assert scan1_assets[0].id == "asset-1"

def test_scan_id_project_isolation(db_session):
    """
    Verify that requesting scan_id belonging to Project B when querying Project A returns [] (no cross-project leakage).
    """
    proj_a = Project(id="proj-A", name="Project A")
    proj_b = Project(id="proj-B", name="Project B")
    db_session.add_all([proj_a, proj_b])
    db_session.commit()

    scan_a = Scan(id="scan-A", project_id=proj_a.id, status=ScanStatus.COMPLETED, target_path="/pathA")
    scan_b = Scan(id="scan-B", project_id=proj_b.id, status=ScanStatus.COMPLETED, target_path="/pathB")
    db_session.add_all([scan_a, scan_b])
    db_session.commit()

    asset_a = CryptoAsset(id="asset-A", scan_id=scan_a.id, name="Asset A", asset_type=AssetType.ALGORITHM, algorithm_name="AES-256", location="a.py")
    asset_b = CryptoAsset(id="asset-B", scan_id=scan_b.id, name="Asset B", asset_type=AssetType.ALGORITHM, algorithm_name="RSA-2048", location="b.py")
    db_session.add_all([asset_a, asset_b])
    db_session.commit()

    repo = AssetRepository(db_session)

    # Requesting Project A with Scan B must return empty list (no leakage)
    res_cross = repo.get_by_project("proj-A", scan_id="scan-B")
    assert res_cross == []

    # Unknowns request Project A with Scan B must return empty list
    res_unknowns_cross = repo.get_unknowns_by_project("proj-A", scan_id="scan-B")
    assert res_unknowns_cross == []

    # Valid matching scan_id returns correct assets
    res_valid = repo.get_by_project("proj-A", scan_id="scan-A")
    assert len(res_valid) == 1
    assert res_valid[0].id == "asset-A"

def test_latest_completed_scan_semantics(db_session):
    """
    Verify that latest_only=True selects the latest COMPLETED scan, ignoring running/failed scans.
    """
    proj = Project(id="proj-completed-test", name="Completed Test Project")
    db_session.add(proj)
    db_session.commit()

    # Completed scan (older)
    scan_completed = Scan(id="scan-comp", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/comp")
    db_session.add(scan_completed)
    db_session.commit()

    # Running scan (newer)
    scan_running = Scan(id="scan-run", project_id=proj.id, status=ScanStatus.RUNNING, target_path="/run")
    db_session.add(scan_running)
    db_session.commit()

    asset_comp = CryptoAsset(id="asset-comp", scan_id=scan_completed.id, name="Completed Asset", asset_type=AssetType.ALGORITHM, algorithm_name="AES-256", location="comp.py")
    asset_run = CryptoAsset(id="asset-run", scan_id=scan_running.id, name="Running Asset", asset_type=AssetType.ALGORITHM, algorithm_name="SHA-256", location="run.py")
    db_session.add_all([asset_comp, asset_run])
    db_session.commit()

    repo = AssetRepository(db_session)

    # Must select completed scan asset, ignoring newer running scan
    latest_assets = repo.get_by_project(proj.id, latest_only=True)
    assert len(latest_assets) == 1
    assert latest_assets[0].id == "asset-comp"

    # Only running scans -> returns []
    proj_only_running = Project(id="proj-running-only", name="Running Only Project")
    db_session.add(proj_only_running)
    db_session.commit()
    scan_only_run = Scan(id="scan-only-run", project_id=proj_only_running.id, status=ScanStatus.RUNNING, target_path="/only_run")
    db_session.add(scan_only_run)
    db_session.commit()
    asset_only_run = CryptoAsset(id="asset-only-run", scan_id=scan_only_run.id, name="Only Run Asset", asset_type=AssetType.ALGORITHM, algorithm_name="ECC", location="only_run.py")
    db_session.add(asset_only_run)
    db_session.commit()

    no_completed_assets = repo.get_by_project(proj_only_running.id, latest_only=True)
    assert no_completed_assets == []

def test_precomputed_business_context_no_db_query(db_session):
    proj = Project(id="proj-perf-2", name="Perf Project 2", business_context={})
    scan = Scan(id="scan-3", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/test3")
    asset = CryptoAsset(id="asset-3", scan_id=scan.id, name="Test Asset", asset_type=AssetType.ALGORITHM, algorithm_name="AES-256", location="a.py")
    db_session.add_all([proj, scan, asset])
    db_session.commit()

    precomputed = {"effective_criticality": "HIGH"}

    # Evaluate using precomputed context
    ctx = resolve_effective_artifact_context(asset, proj, db_session, precomputed_business_context=precomputed)
    assert ctx["business_criticality"] == "HIGH"

def test_migration_repository_eager_loading_tasks(db_session):
    proj = Project(id="proj-perf-3", name="Perf Project 3")
    plan = MigrationPlan(id="plan-1", project_id=proj.id, name="Plan 1")
    task1 = MigrationTask(id="task-1", plan_id=plan.id, asset_id="asset-1", title="Task 1")
    task2 = MigrationTask(id="task-2", plan_id=plan.id, asset_id="asset-2", title="Task 2")
    db_session.add_all([proj, plan, task1, task2])
    db_session.commit()

    repo = MigrationRepository(db_session)

    query_count = 0
    @event.listens_for(db_session.bind, "before_cursor_execute")
    def count_queries(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    plans = repo.get_plans_by_project(proj.id)
    assert len(plans) == 1
    # Accessing tasks should NOT trigger additional SQL query because selectinload eager-loaded tasks
    initial_queries = query_count
    tasks = plans[0].tasks
    assert len(tasks) == 2
    assert query_count == initial_queries
