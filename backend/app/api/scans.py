from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.scan_repository import ScanRepository
from app.models.schemas import ScanCreate, ScanResponse
from app.models.enums import ScanStatus
from app.orchestration.job_manager import dispatch_scan_job

router = APIRouter(tags=["Scans"])

@router.post("/projects/{project_id}/scans", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
def start_scan(project_id: str, scan_in: ScanCreate, db: Session = Depends(get_db)):
    repo = ScanRepository(db)
    scan = repo.create(project_id=project_id, target_path=scan_in.target_path, scan_type=scan_in.scan_type)
    dispatch_scan_job(scan.id)
    return scan

@router.get("/projects/{project_id}/scans", response_model=List[ScanResponse])
def get_project_scans(project_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = ScanRepository(db)
    return repo.get_by_project(project_id, skip=skip, limit=limit)

@router.get("/scans/{scan_id}", response_model=ScanResponse)
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    repo = ScanRepository(db)
    scan = repo.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@router.post("/scans/{scan_id}/cancel", response_model=ScanResponse)
def cancel_scan(scan_id: str, db: Session = Depends(get_db)):
    repo = ScanRepository(db)
    scan = repo.update_status(scan_id, ScanStatus.CANCELLED, error_message="Scan cancelled by user")
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@router.post("/scans/{scan_id}/rerun", response_model=ScanResponse)
def rerun_scan(scan_id: str, db: Session = Depends(get_db)):
    repo = ScanRepository(db)
    old_scan = repo.get(scan_id)
    if not old_scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    new_scan = repo.create(project_id=old_scan.project_id, target_path=old_scan.target_path, scan_type=old_scan.scan_type)
    dispatch_scan_job(new_scan.id)
    return new_scan

@router.post("/scans/{scan_id}/inputs/source", response_model=ScanResponse)
def input_source_scan(scan_id: str, db: Session = Depends(get_db)):
    repo = ScanRepository(db)
    scan = repo.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    dispatch_scan_job(scan_id)
    return scan
