from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.orchestration.scan_orchestrator import ScanOrchestrator
from app.core.logging import logger

executor = ThreadPoolExecutor(max_workers=4)

def _execute_scan_in_background(scan_id: str):
    db: Session = SessionLocal()
    try:
        orchestrator = ScanOrchestrator()
        orchestrator.run_scan(scan_id, db)
    finally:
        db.close()

def dispatch_scan_job(scan_id: str):
    logger.info(f"Dispatching background scan job for scan ID {scan_id}")
    executor.submit(_execute_scan_in_background, scan_id)
