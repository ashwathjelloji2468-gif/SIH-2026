from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.scan_repository import ScanRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.project_repository import ProjectRepository
from app.cbom.validator import CBOMValidator
from app.reports.report_generator import ReportGenerator

router = APIRouter(tags=["Reports & CBOM"])

@router.get("/scans/{scan_id}/cbom")
def get_scan_cbom(scan_id: str, db: Session = Depends(get_db)):
    repo = ScanRepository(db)
    scan = repo.get(scan_id)
    if not scan or not scan.cbom_json:
        raise HTTPException(status_code=404, detail="CBOM not found for this scan")
    return scan.cbom_json

@router.post("/scans/{scan_id}/cbom/validate")
def validate_scan_cbom(scan_id: str, db: Session = Depends(get_db)):
    repo = ScanRepository(db)
    scan = repo.get(scan_id)
    if not scan or not scan.cbom_json:
        raise HTTPException(status_code=404, detail="CBOM not found")
    validator = CBOMValidator()
    is_valid = validator.validate(scan.cbom_json)
    return {"scan_id": scan_id, "valid": is_valid, "specVersion": "1.5"}

@router.get("/scans/{scan_id}/cbom/download")
def download_scan_cbom(scan_id: str, db: Session = Depends(get_db)):
    repo = ScanRepository(db)
    scan = repo.get(scan_id)
    if not scan or not scan.cbom_json:
        raise HTTPException(status_code=404, detail="CBOM not found")
    return JSONResponse(
        content=scan.cbom_json,
        headers={"Content-Disposition": f'attachment; filename="cbom-{scan_id}.json"'}
    )

@router.post("/projects/{project_id}/reports")
def create_project_report(project_id: str, db: Session = Depends(get_db)):
    proj_repo = ProjectRepository(db)
    asset_repo = AssetRepository(db)
    
    proj = proj_repo.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    assets = asset_repo.get_by_project(project_id)
    generator = ReportGenerator()
    report = generator.generate_project_report(proj.name, assets)
    report["report_id"] = f"rep-{project_id}"
    return report

@router.get("/reports/{report_id}")
def get_report(report_id: str):
    return {"report_id": report_id, "status": "READY"}

@router.get("/reports/{report_id}/download")
def download_report(report_id: str):
    return {"report_id": report_id, "download_url": f"/api/v1/reports/{report_id}/file"}
