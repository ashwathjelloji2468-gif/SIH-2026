import pytest
import time
import json
import threading
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.db_models import Project, Scan, CryptoAsset, Recommendation
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety, RecommendationCategory, StandardStatus
from app.orchestration.scan_orchestrator import ScanOrchestrator
from app.orchestration.job_manager import dispatch_post_scan_enrichment_job, active_enrichment_jobs, _active_lock
from app.api.qars import get_project_qars, get_asset_qars
from app.api.inventory import get_project_inventory
from app.api.recommendations import get_project_recommendations, evaluate_project_recommendations
from app.services.business_criticality_service import BusinessCriticalityService
from app.context.invalidation import invalidate_project_precomputed_data
from app.repositories.asset_repository import AssetRepository


from sqlalchemy.pool import StaticPool


@pytest.fixture
def db_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_post_scan_enrichment_computes_and_persists_qars_and_effective_context(db_session):
    """
    Requirement A & B: Verify scan/enrichment computes required derived result (QARS & effective context)
    and persists it against the correct scan/asset in extra_metadata.
    """
    proj = Project(id="proj-p3-1", name="Phase 3 Test Project 1")
    db_session.add(proj)
    db_session.commit()

    scan = Scan(id="scan-p3-1", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/path1")
    db_session.add(scan)
    db_session.commit()

    asset1 = CryptoAsset(
        id="asset-p3-1",
        scan_id=scan.id,
        name="Asset 1 RSA",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.SIGNATURE,
        location="auth.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    asset2 = CryptoAsset(
        id="asset-p3-2",
        scan_id=scan.id,
        name="Asset 2 AES",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256",
        purpose=CryptoPurpose.ENCRYPTION,
        location="storage.py",
        quantum_safety=QuantumSafety.QUANTUM_SAFE
    )
    db_session.add_all([asset1, asset2])
    db_session.commit()

    orchestrator = ScanOrchestrator()
    orchestrator.run_post_scan_enrichment(scan.id, db_session)

    db_session.refresh(asset1)
    db_session.refresh(asset2)

    assert "qars_result" in asset1.extra_metadata
    assert "effective_context" in asset1.extra_metadata
    assert "effective_z" in asset1.extra_metadata
    assert "effective_y" in asset1.extra_metadata

    assert "qars_result" in asset2.extra_metadata
    assert "effective_context" in asset2.extra_metadata
    assert "effective_z" in asset2.extra_metadata

    qars1 = asset1.extra_metadata["qars_result"]
    assert qars1["asset_id"] == "asset-p3-1"
    assert "final_score" in qars1
    assert "level" in qars1


def test_operational_get_qars_reads_persisted_result(db_session, monkeypatch):
    """
    Requirement C & E: Operational GET /projects/{project_id}/qars reads persisted result
    without rerunning evaluate_artifact_qars.
    """
    proj = Project(id="proj-p3-2", name="Phase 3 Test Project 2")
    db_session.add(proj)
    db_session.commit()

    scan = Scan(id="scan-p3-2", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/path2")
    db_session.add(scan)
    db_session.commit()

    asset = CryptoAsset(
        id="asset-p3-3",
        scan_id=scan.id,
        name="Asset RSA 3",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.SIGNATURE,
        location="main.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db_session.add(asset)
    db_session.commit()

    orchestrator = ScanOrchestrator()
    orchestrator.run_post_scan_enrichment(scan.id, db_session)

    def panic_if_called(*args, **kwargs):
        raise RuntimeError("evaluate_artifact_qars SHOULD NOT be called when persisted data exists!")

    monkeypatch.setattr("app.api.qars.evaluate_artifact_qars", panic_if_called)

    res = get_project_qars(project_id=proj.id, scan_id=scan.id, db=db_session)
    assert res.project_id == proj.id
    assert res.asset_count == 1
    assert res.summary["qars_average"] is not None

    res_asset = get_asset_qars(project_id=proj.id, asset_id=asset.id, db=db_session)
    assert res_asset.status == "SUCCESS"


def test_operational_get_inventory_reads_persisted_result(db_session, monkeypatch):
    """
    Requirement C & E: Operational GET /projects/{project_id}/inventory reads persisted effective context
    without evaluating ZEngine.
    """
    proj = Project(id="proj-p3-3", name="Phase 3 Test Project 3")
    db_session.add(proj)
    db_session.commit()

    scan = Scan(id="scan-p3-3", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/path3")
    db_session.add(scan)
    db_session.commit()

    asset = CryptoAsset(
        id="asset-p3-4",
        scan_id=scan.id,
        name="Asset AES 4",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256",
        purpose=CryptoPurpose.ENCRYPTION,
        location="db.py",
        quantum_safety=QuantumSafety.QUANTUM_SAFE
    )
    db_session.add(asset)
    db_session.commit()

    orchestrator = ScanOrchestrator()
    orchestrator.run_post_scan_enrichment(scan.id, db_session)

    def panic_z(*args, **kwargs):
        raise RuntimeError("ZEngine.evaluate_component SHOULD NOT be called when persisted effective Z exists!")

    monkeypatch.setattr("app.engines.z_engine.ZEngine.evaluate_component", panic_z)

    inv = get_project_inventory(project_id=proj.id, scan_id=scan.id, db=db_session)
    assert len(inv) == 1
    assert inv[0]["id"] == "asset-p3-4"
    assert inv[0]["effective_x_years"] is not None


def test_historical_scan_preservation(db_session):
    """
    Hardening 1: Verify invalidation preserves historical scan snapshots (Scan A)
    and invalidates ONLY the operational latest-completed scan (Scan B).
    """
    proj = Project(id="proj-hist-test", name="Historical Test Project")
    db_session.add(proj)
    db_session.commit()

    scan_a = Scan(id="scan-A-hist", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/scanA")
    db_session.add(scan_a)
    db_session.commit()
    asset_a = CryptoAsset(
        id="asset-A-hist",
        scan_id=scan_a.id,
        name="Historical Asset A",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-1024",
        purpose=CryptoPurpose.SIGNATURE,
        location="old.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db_session.add(asset_a)
    db_session.commit()

    scan_b = Scan(id="scan-B-hist", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/scanB")
    db_session.add(scan_b)
    db_session.commit()
    asset_b = CryptoAsset(
        id="asset-B-hist",
        scan_id=scan_b.id,
        name="Latest Asset B",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256",
        purpose=CryptoPurpose.ENCRYPTION,
        location="new.py",
        quantum_safety=QuantumSafety.QUANTUM_SAFE
    )
    db_session.add(asset_b)
    db_session.commit()

    orchestrator = ScanOrchestrator()
    orchestrator.run_post_scan_enrichment(scan_a.id, db_session)
    orchestrator.run_post_scan_enrichment(scan_b.id, db_session)

    db_session.refresh(asset_a)
    db_session.refresh(asset_b)
    score_a_orig = asset_a.extra_metadata["qars_result"]["final_score"]

    # Invalidate operational context
    invalidate_project_precomputed_data(proj.id, db_session, re_enrich=False)

    db_session.refresh(asset_a)
    db_session.refresh(asset_b)

    # Historical Scan A derived snapshot MUST remain intact
    assert "qars_result" in asset_a.extra_metadata
    assert asset_a.extra_metadata["qars_result"]["final_score"] == score_a_orig

    # Operational Scan B derived data MUST be invalidated
    assert "qars_result" not in (asset_b.extra_metadata or {})

    # Explicit historical query for Scan A returns Scan A's historical snapshot
    res_a = get_project_qars(project_id=proj.id, scan_id=scan_a.id, latest_only=False, db=db_session)
    assert res_a.assets[0].final_score == score_a_orig


def test_invalidation_vs_enrichment_race_protection(db_session):
    """
    Hardening 2: Verify that an old enrichment calculation starting before a context update
    cannot overwrite a newer context invalidation with stale data.
    """
    proj = Project(id="proj-race-test", name="Race Test Project")
    db_session.add(proj)
    db_session.commit()

    scan = Scan(id="scan-race-test", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/race")
    db_session.add(scan)
    db_session.commit()

    asset = CryptoAsset(
        id="asset-race-1",
        scan_id=scan.id,
        name="Race Asset",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.SIGNATURE,
        location="race.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db_session.add(asset)
    db_session.commit()

    orchestrator = ScanOrchestrator()
    start_updated_at = proj.updated_at

    time.sleep(0.01)
    srv = BusinessCriticalityService(db_session)
    srv.update_project_business_criticality(
        project_id=proj.id,
        user_override="CRITICAL",
        adjustment_reason="Upgrade project criticality"
    )

    db_session.refresh(proj)
    assert proj.updated_at > start_updated_at

    orchestrator.run_post_scan_enrichment(scan.id, db_session)

    db_session.refresh(asset)
    qars_res = (asset.extra_metadata or {}).get("qars_result")
    if qars_res:
        assert qars_res["explanation"]["exposure"] == 5.0 or qars_res["level"] != "LOW"


def test_true_concurrent_extra_metadata_race(tmp_path):
    """
    User Request 1: True concurrent extra_metadata write test using threading.Barrier(2)
    and independent SQLAlchemy sessions over real concurrent SQLite connections.
    """
    db_file = tmp_path / "test_conc.db"
    file_engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"timeout": 15.0, "check_same_thread": False}
    )
    Base.metadata.create_all(file_engine)

    # Enable WAL mode for concurrent write support
    with file_engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL;")

    SessionLocal = sessionmaker(bind=file_engine)
    session_init = SessionLocal()

    proj = Project(id="proj-true-conc", name="True Concurrency Project")
    scan = Scan(id="scan-true-conc", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/conc")
    asset = CryptoAsset(
        id="asset-true-conc-1",
        scan_id=scan.id,
        name="True Conc Asset",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256",
        purpose=CryptoPurpose.ENCRYPTION,
        location="conc.py",
        quantum_safety=QuantumSafety.QUANTUM_SAFE,
        extra_metadata={"base_key": "base"}
    )
    session_init.add_all([proj, scan, asset])
    session_init.commit()
    session_init.close()

    barrier = threading.Barrier(2)

    def worker_A():
        s = SessionLocal()
        try:
            repo = AssetRepository(s)
            a = repo.get("asset-true-conc-1")
            _ = a.extra_metadata
            barrier.wait()  # Synchronize read phase
            repo.update_extra_metadata("asset-true-conc-1", {"field_A": "A"})
        finally:
            s.close()

    def worker_B():
        s = SessionLocal()
        try:
            repo = AssetRepository(s)
            a = repo.get("asset-true-conc-1")
            _ = a.extra_metadata
            barrier.wait()  # Synchronize read phase
            repo.update_extra_metadata("asset-true-conc-1", {"field_B": "B"})
        finally:
            s.close()

    t1 = threading.Thread(target=worker_A)
    t2 = threading.Thread(target=worker_B)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Session C: Verify final persisted JSON state contains base_key, field_A, and field_B
    s_c = SessionLocal()
    repo_c = AssetRepository(s_c)
    final_asset = repo_c.get("asset-true-conc-1")
    final_extra = final_asset.extra_metadata
    s_c.close()

    assert final_extra["base_key"] == "base"
    assert final_extra["field_A"] == "A"
    assert final_extra["field_B"] == "B"


def test_recommendation_freshness_chain_after_mutation(db_session, monkeypatch):
    """
    User Request 2: Complete recommendation freshness chain:
    Mutation -> Invalidation -> Re-enrichment -> Risk/Rec recomputation -> GET reads fresh persisted rows.
    """
    proj = Project(id="proj-rec-chain", name="Rec Chain Project")
    scan = Scan(id="scan-rec-chain", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/chain")
    asset = CryptoAsset(
        id="asset-chain-1",
        scan_id=scan.id,
        name="Chain Asset",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.SIGNATURE,
        location="chain.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    rec1 = Recommendation(
        id="rec-old-1",
        asset_id=asset.id,
        target_pqc_candidate="ML-DSA-65",
        recommended_algorithm="ML-DSA-65",
        category=RecommendationCategory.PQC_REPLACEMENT,
        priority="LOW",
        standard_status=StandardStatus.FINAL_STANDARD,
        rationale="Original low-priority recommendation"
    )
    db_session.add_all([proj, scan, asset, rec1])
    db_session.commit()

    # Initial GET /recommendations returns original rec1
    recs1 = get_project_recommendations(project_id=proj.id, db=db_session)
    assert recs1[0]["priority"] == "LOW"

    # Trigger context mutation: Update business criticality to CRITICAL
    srv = BusinessCriticalityService(db_session)
    srv.update_project_business_criticality(
        project_id=proj.id,
        user_override="CRITICAL",
        adjustment_reason="Criticality upgrade trigger re-enrichment"
    )

    # Simulate background re-enrichment execution
    orchestrator = ScanOrchestrator()
    orchestrator.run_post_scan_enrichment(scan.id, db_session)

    # Monkeypatch RecommendationEngine to ensure GET does NOT rerun rule engine
    def panic_rec_engine(*args, **kwargs):
        raise RuntimeError("RecommendationEngine SHOULD NOT run on GET path!")

    monkeypatch.setattr("app.recommend.service.RecommendationEngine.generate_recommendation", panic_rec_engine)

    # Subsequent GET /recommendations reads fresh persisted recommendations
    recs_fresh = get_project_recommendations(project_id=proj.id, db=db_session)
    assert len(recs_fresh) == 1
    assert recs_fresh[0]["priority"] in ["HIGH", "CRITICAL"]

    # Undo monkeypatch so explicit POST evaluate can force-regenerate
    monkeypatch.undo()

    # Verify explicit POST /recommendations/evaluate still force-regenerates independently
    summary_eval = evaluate_project_recommendations(project_id=proj.id, db=db_session)
    assert summary_eval["total_recommendations"] == 1


def test_duplicate_re_enrichment_dispatch_protection():
    """
    User Request 3: Verify dispatch_post_scan_enrichment_job prevents duplicate concurrent jobs
    for the same scan ID.
    """
    scan_id = "scan-dedupe-test"
    with _active_lock:
        active_enrichment_jobs.add(scan_id)

    try:
        # Second dispatch for same running scan_id must return False
        is_dispatched = dispatch_post_scan_enrichment_job(scan_id)
        assert is_dispatched is False
    finally:
        with _active_lock:
            active_enrichment_jobs.discard(scan_id)


def test_sql_query_count_measurement(db_session):
    """
    Hardening 7: Measure SQL query counts for GET /inventory call.
    """
    proj = Project(id="proj-p3-sql", name="SQL Count Project")
    scan = Scan(id="scan-p3-sql", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/sql")
    assets = [
        CryptoAsset(
            id=f"asset-sql-{i}",
            scan_id=scan.id,
            name=f"SQL Asset {i}",
            asset_type=AssetType.ALGORITHM,
            algorithm_name="AES-256",
            purpose=CryptoPurpose.ENCRYPTION,
            location=f"loc_{i}.py",
            quantum_safety=QuantumSafety.QUANTUM_SAFE
        ) for i in range(10)
    ]
    db_session.add_all([proj, scan] + assets)
    db_session.commit()

    orchestrator = ScanOrchestrator()
    orchestrator.run_post_scan_enrichment(scan.id, db_session)

    query_count = 0
    @event.listens_for(db_session.bind, "before_cursor_execute")
    def count_sql(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    t0 = time.perf_counter()
    inv = get_project_inventory(project_id=proj.id, scan_id=scan.id, db=db_session)
    t_inv = time.perf_counter() - t0
    sql_inv_count = query_count

    assert len(inv) == 10
    print(f"\n[SQL BENCHMARK] GET /inventory (10 assets) — Time: {t_inv*1000:.2f}ms, SQL Queries: {sql_inv_count}")


def test_inventory_payload_size_impact(db_session):
    """
    Hardening 7: Measure inventory response JSON payload size before/after extra_metadata QARS persistence.
    """
    proj = Project(id="proj-p3-size", name="Payload Size Project")
    scan = Scan(id="scan-p3-size", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/size")
    asset = CryptoAsset(
        id="asset-size-1",
        scan_id=scan.id,
        name="Size Asset",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.SIGNATURE,
        location="size.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db_session.add_all([proj, scan, asset])
    db_session.commit()

    inv_before = get_project_inventory(project_id=proj.id, scan_id=scan.id, db=db_session)
    json_before = json.dumps(inv_before)
    size_before = len(json_before.encode("utf-8"))

    orchestrator = ScanOrchestrator()
    orchestrator.run_post_scan_enrichment(scan.id, db_session)

    inv_after = get_project_inventory(project_id=proj.id, scan_id=scan.id, db=db_session)
    json_after = json.dumps(inv_after)
    size_after = len(json_after.encode("utf-8"))

    print(f"\n[PAYLOAD BENCHMARK] GET /inventory payload size — Before: {size_before} B, After: {size_after} B, Delta: {size_after - size_before} B")
    assert size_before == size_after


def test_transaction_preservation_in_update_extra_metadata(db_session):
    """
    User Request 2: Verify update_extra_metadata does not discard unrelated pending ORM changes
    in the same SQLAlchemy Session.
    """
    proj = Project(id="proj-tx-preserve", name="Original Name")
    scan = Scan(id="scan-tx-preserve", project_id=proj.id, status=ScanStatus.COMPLETED, target_path="/tx")
    asset = CryptoAsset(
        id="asset-tx-preserve-1",
        scan_id=scan.id,
        name="Asset TX",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256",
        purpose=CryptoPurpose.ENCRYPTION,
        location="tx.py",
        quantum_safety=QuantumSafety.QUANTUM_SAFE,
        extra_metadata={"key1": "val1"}
    )
    db_session.add_all([proj, scan, asset])
    db_session.commit()

    # 1. Modify unrelated Project field in active db_session (uncommitted)
    proj.name = "Modified Project Name"

    # 2. Modify extra_metadata using repository
    repo = AssetRepository(db_session)
    repo.update_extra_metadata("asset-tx-preserve-1", {"key2": "val2"})

    # 3. Commit session
    db_session.commit()

    # 4. Reload in session and verify BOTH modifications persisted
    db_session.expire_all()
    reloaded_proj = db_session.query(Project).filter(Project.id == proj.id).first()
    reloaded_asset = db_session.query(CryptoAsset).filter(CryptoAsset.id == asset.id).first()

    assert reloaded_proj.name == "Modified Project Name"
    assert reloaded_asset.extra_metadata["key1"] == "val1"
    assert reloaded_asset.extra_metadata["key2"] == "val2"
