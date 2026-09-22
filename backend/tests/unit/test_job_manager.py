import time
from unittest.mock import patch, MagicMock
from app.core.config import settings
from app.orchestration.job_manager import (
    dispatch_scan_job,
    dispatch_post_scan_enrichment_job,
    active_scan_jobs,
    active_enrichment_jobs,
    executor,
)


def test_job_manager_duplicate_scan_dispatch_prevention():
    scan_id = "test-scan-dup-1"

    def slow_scan(s_id, db):
        time.sleep(0.2)

    with patch("app.orchestration.scan_orchestrator.ScanOrchestrator.run_scan", side_effect=slow_scan), \
         patch("app.orchestration.scan_orchestrator.ScanOrchestrator.run_post_scan_enrichment"):

        first_dispatch = dispatch_scan_job(scan_id)
        second_dispatch = dispatch_scan_job(scan_id)

        assert first_dispatch is True
        assert second_dispatch is False

        # Wait for job to clear
        time.sleep(0.3)
        assert scan_id not in active_scan_jobs


def test_job_manager_duplicate_enrichment_dispatch_prevention():
    scan_id = "test-enrich-dup-1"

    def slow_enrichment(s_id, db):
        time.sleep(0.2)

    with patch("app.orchestration.scan_orchestrator.ScanOrchestrator.run_post_scan_enrichment", side_effect=slow_enrichment):
        first_dispatch = dispatch_post_scan_enrichment_job(scan_id)
        second_dispatch = dispatch_post_scan_enrichment_job(scan_id)

        assert first_dispatch is True
        assert second_dispatch is False

        # Wait for job to clear
        time.sleep(0.3)
        assert scan_id not in active_enrichment_jobs


def test_job_manager_max_workers_bounded():
    assert executor._max_workers == settings.SCAN_MAX_WORKERS
    assert settings.SCAN_MAX_WORKERS == 2
