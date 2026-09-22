import threading
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.orchestration.scan_orchestrator import ScanOrchestrator
from app.core.logging import logger

executor = ThreadPoolExecutor(max_workers=settings.SCAN_MAX_WORKERS)
_active_lock = threading.Lock()
active_scan_jobs = set()
active_enrichment_jobs = set()


def _execute_enrichment_in_background(scan_id: str):
    try:
        db: Session = SessionLocal()
        try:
            orchestrator = ScanOrchestrator()
            orchestrator.run_post_scan_enrichment(scan_id, db)
        except Exception as e:
            logger.error(f"Error executing enrichment for scan {scan_id}: {e}", exc_info=True)
        finally:
            db.close()
    finally:
        with _active_lock:
            active_enrichment_jobs.discard(scan_id)


def dispatch_post_scan_enrichment_job(scan_id: str) -> bool:
    with _active_lock:
        if scan_id in active_enrichment_jobs:
            logger.warning(f"Enrichment job for scan ID {scan_id} is already running. Skipping duplicate dispatch.")
            return False
        active_enrichment_jobs.add(scan_id)

    logger.info(f"Dispatching background post-scan enrichment job for scan ID {scan_id}")
    executor.submit(_execute_enrichment_in_background, scan_id)
    return True


def _execute_scan_in_background(scan_id: str):
    try:
        db: Session = SessionLocal()
        try:
            orchestrator = ScanOrchestrator()
            orchestrator.run_scan(scan_id, db)
        except Exception as e:
            logger.error(f"Error executing scan {scan_id}: {e}", exc_info=True)
        finally:
            db.close()

        # Core scan completed and DB session closed; dispatch post-scan enrichment asynchronously
        dispatch_post_scan_enrichment_job(scan_id)
    finally:
        with _active_lock:
            active_scan_jobs.discard(scan_id)


def dispatch_scan_job(scan_id: str) -> bool:
    with _active_lock:
        if scan_id in active_scan_jobs:
            logger.warning(f"Scan job for scan ID {scan_id} is already running. Skipping duplicate dispatch.")
            return False
        active_scan_jobs.add(scan_id)

    logger.info(f"Dispatching background scan job for scan ID {scan_id}")
    executor.submit(_execute_scan_in_background, scan_id)
    return True
