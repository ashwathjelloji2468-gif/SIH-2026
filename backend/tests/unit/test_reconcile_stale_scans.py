from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.database import Base
from app.models.db_models import Project, Scan
from app.models.enums import ScanStatus
from app.repositories.scan_repository import ScanRepository, STALE_ERROR_MESSAGE


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def test_reconcile_stale_scans_rules(db_session: Session):
    repo = ScanRepository(db_session)
    now = datetime.now(timezone.utc)

    # Setup project
    proj = Project(name="Reconcile Test Project")
    db_session.add(proj)
    db_session.commit()
    db_session.refresh(proj)

    # TEST 1: RUNNING scan created 5 minutes ago -> remains RUNNING
    scan_5m = Scan(
        project_id=proj.id,
        target_path="/tmp/test_5m",
        status=ScanStatus.RUNNING,
        created_at=now - timedelta(minutes=5),
    )
    # TEST 2: RUNNING scan created 29 minutes ago -> remains RUNNING
    scan_29m = Scan(
        project_id=proj.id,
        target_path="/tmp/test_29m",
        status=ScanStatus.RUNNING,
        created_at=now - timedelta(minutes=29),
    )
    # TEST 3: RUNNING scan created 30+ minutes ago (e.g. 35m) -> becomes FAILED
    scan_35m = Scan(
        project_id=proj.id,
        target_path="/tmp/test_35m",
        status=ScanStatus.RUNNING,
        created_at=now - timedelta(minutes=35),
    )
    # TEST 6: COMPLETED scan is never modified
    scan_completed = Scan(
        project_id=proj.id,
        target_path="/tmp/test_comp",
        status=ScanStatus.COMPLETED,
        created_at=now - timedelta(days=5),
        completed_at=now - timedelta(days=5),
    )
    # TEST 7: FAILED scan is never modified
    scan_failed = Scan(
        project_id=proj.id,
        target_path="/tmp/test_failed",
        status=ScanStatus.FAILED,
        created_at=now - timedelta(days=5),
        completed_at=now - timedelta(days=5),
        error_message="Original failure",
    )
    # TEST 8: CANCELLED scan is never modified
    scan_cancelled = Scan(
        project_id=proj.id,
        target_path="/tmp/test_cancelled",
        status=ScanStatus.CANCELLED,
        created_at=now - timedelta(days=5),
        completed_at=now - timedelta(days=5),
        error_message="User cancelled",
    )

    db_session.add_all(
        [scan_5m, scan_29m, scan_35m, scan_completed, scan_failed, scan_cancelled]
    )
    db_session.commit()

    # Trigger reconciliation via get_by_project
    scans_after = repo.get_by_project(proj.id)
    scan_dict = {s.id: s for s in scans_after}

    # TEST 1 verification: 5m scan remains RUNNING
    assert scan_dict[scan_5m.id].status == ScanStatus.RUNNING
    assert scan_dict[scan_5m.id].completed_at is None

    # TEST 2 verification: 29m scan remains RUNNING
    assert scan_dict[scan_29m.id].status == ScanStatus.RUNNING
    assert scan_dict[scan_29m.id].completed_at is None

    # TEST 3 verification: 35m scan becomes FAILED
    assert scan_dict[scan_35m.id].status == ScanStatus.FAILED

    # TEST 4 verification: stale scan gets completed_at populated
    assert scan_dict[scan_35m.id].completed_at is not None

    # TEST 5 verification: stale scan gets exact reconciliation error message
    assert scan_dict[scan_35m.id].error_message == STALE_ERROR_MESSAGE

    # TEST 6 verification: COMPLETED scan is never modified
    assert scan_dict[scan_completed.id].status == ScanStatus.COMPLETED

    # TEST 7 verification: FAILED scan is never modified
    assert scan_dict[scan_failed.id].status == ScanStatus.FAILED
    assert scan_dict[scan_failed.id].error_message == "Original failure"

    # TEST 8 verification: CANCELLED scan is never modified
    assert scan_dict[scan_cancelled.id].status == ScanStatus.CANCELLED
    assert scan_dict[scan_cancelled.id].error_message == "User cancelled"

    # TEST 9 verification: idempotency; an already FAILED scan is not changed again
    reconciled_second_time = repo.reconcile_stale_scans(proj.id)
    assert len(reconciled_second_time) == 0
    db_session.refresh(scan_35m)
    assert scan_35m.status == ScanStatus.FAILED
    assert scan_35m.error_message == STALE_ERROR_MESSAGE


def test_existing_orphan_example(db_session: Session):
    # Regression scenario matching orphan example:
    # scan: 0c941552-a452-4233-aa51-38e125e8f227 created on 2026-09-08 13:12:59
    repo = ScanRepository(db_session)
    proj = Project(name="Orphan Regression Project")
    db_session.add(proj)
    db_session.commit()

    orphan_scan = Scan(
        id="0c941552-a452-4233-aa51-38e125e8f227",
        project_id=proj.id,
        target_path="/tmp/demo-bank",
        status=ScanStatus.RUNNING,
        created_at=datetime(2026, 9, 8, 13, 12, 59, tzinfo=timezone.utc),
    )
    db_session.add(orphan_scan)
    db_session.commit()

    scans = repo.get_by_project(proj.id)
    target = next((s for s in scans if s.id == orphan_scan.id), None)
    assert target is not None
    assert target.status == ScanStatus.FAILED
    assert target.completed_at is not None
    assert target.error_message == STALE_ERROR_MESSAGE
