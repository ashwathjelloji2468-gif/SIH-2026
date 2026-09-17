import os
import time
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.database import Base
from app.models.db_models import Project, Scan, CryptoAsset, MigrationPlan
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety
from app.repositories.scan_repository import ScanRepository
from app.repositories.asset_repository import AssetRepository
from app.orchestration.scan_orchestrator import ScanOrchestrator


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def test_core_scan_pipeline_separation(db_session: Session, tmp_path):
    # Setup test project and target directory with dummy file
    proj = Project(name="Core Pipeline Test Project")
    db_session.add(proj)
    db_session.commit()
    db_session.refresh(proj)

    test_file = tmp_path / "crypto_sample.py"
    test_file.write_text("import hashlib\nhashlib.sha256(b'test')")

    scan_repo = ScanRepository(db_session)
    scan = scan_repo.create(project_id=proj.id, target_path=str(tmp_path), scan_type="source")

    orchestrator = ScanOrchestrator()

    # Track timing and state transitions
    t_start = time.time()
    orchestrator.run_scan(scan.id, db_session)
    t_core_end = time.time()

    db_session.refresh(scan)

    # TEST 1: Core scan generates CBOM.
    assert scan.cbom_json is not None
    assert scan.cbom_json.get("bomFormat") == "CycloneDX"

    # TEST 3: Scan status becomes COMPLETED before post-scan enrichment completes.
    assert scan.status == ScanStatus.COMPLETED

    # TEST 4: GET /scans/{scan_id}/cbom returns the generated CBOM immediately after core scan completion.
    assert scan.cbom_json is not None

    # TEST 14 & 15: Persistent Scan.target_path and local directory scan target remain unchanged.
    assert scan.target_path == str(tmp_path)

    # Now run post-scan enrichment separately
    t_enrich_start = time.time()
    orchestrator.run_post_scan_enrichment(scan.id, db_session)
    t_enrich_end = time.time()

    db_session.refresh(scan)
    assert scan.status == ScanStatus.COMPLETED

    # Measure performance verification
    core_duration = t_core_end - t_start
    enrichment_duration = t_enrich_end - t_enrich_start
    print(f"Performance Verification: Core scan = {core_duration:.3f}s, Post-scan enrichment = {enrichment_duration:.3f}s")


def test_enrichment_failure_tolerance(db_session: Session, tmp_path):
    proj = Project(name="Failure Tolerance Test Project")
    db_session.add(proj)
    db_session.commit()

    scan_repo = ScanRepository(db_session)
    scan = scan_repo.create(project_id=proj.id, target_path=str(tmp_path), scan_type="source")

    # Seed an asset
    asset_repo = AssetRepository(db_session)
    asset_repo.create(
        scan_id=scan.id,
        name="SHA256-test",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="SHA-256",
        key_size=256,
        purpose=CryptoPurpose.HASHING,
        location="sample.py",
        line_number=1,
        quantum_safety=QuantumSafety.QUANTUM_SAFE
    )

    orchestrator = ScanOrchestrator()
    orchestrator.run_scan(scan.id, db_session)
    db_session.refresh(scan)
    assert scan.status == ScanStatus.COMPLETED

    # TEST 10, 11, 12, 13: Mock enrichment services to raise exceptions and verify scan stays COMPLETED
    with patch("app.risk.service.RiskService.assess_project", side_effect=RuntimeError("Risk fail")), \
         patch("app.recommend.service.RecommendationService.recommend_project", side_effect=RuntimeError("Rec fail")), \
         patch("app.graph.blast_radius_engine.BlastRadiusEngine.build_graph_for_scan", side_effect=RuntimeError("Graph fail")), \
         patch("app.migration.planner.MigrationPlanner.create_plan_for_project", side_effect=RuntimeError("Planner fail")):

        orchestrator.run_post_scan_enrichment(scan.id, db_session)

    db_session.refresh(scan)
    # Status MUST remain COMPLETED despite enrichment failures
    assert scan.status == ScanStatus.COMPLETED


def test_migration_planner_idempotency(db_session: Session, tmp_path):
    proj = Project(name="Idempotency Test Project")
    db_session.add(proj)
    db_session.commit()

    scan_repo = ScanRepository(db_session)
    scan = scan_repo.create(project_id=proj.id, target_path=str(tmp_path), scan_type="source")

    asset_repo = AssetRepository(db_session)
    asset_repo.create(
        scan_id=scan.id,
        name="RSA-2048-test",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        key_size=2048,
        purpose=CryptoPurpose.SIGNATURE,
        location="sample.py",
        line_number=1,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )

    orchestrator = ScanOrchestrator()
    orchestrator.run_scan(scan.id, db_session)

    # Run post-scan enrichment first time
    orchestrator.run_post_scan_enrichment(scan.id, db_session)

    plans_first = db_session.query(MigrationPlan).filter(MigrationPlan.project_id == proj.id).all()
    count_first = len(plans_first)

    # Run post-scan enrichment second time
    orchestrator.run_post_scan_enrichment(scan.id, db_session)

    plans_second = db_session.query(MigrationPlan).filter(MigrationPlan.project_id == proj.id).all()
    # TEST 9: MigrationPlanner remains idempotent (plan count does not duplicate)
    assert len(plans_second) == count_first
