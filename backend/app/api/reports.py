from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.scan_repository import ScanRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.project_repository import ProjectRepository
from app.cbom.validator import CBOMValidator
from app.cbom.cyclonedx_adapter import generate_cbom_json
from app.reports.report_generator import ReportGenerator
from app.risk.service import RiskService
from app.engines.mosca_engine import MoscaEngine
from app.recommend.service import RecommendationService

router = APIRouter(tags=["Reports & CBOM"])

@router.get("/scans/{scan_id}/cbom")
def get_scan_cbom(scan_id: str, db: Session = Depends(get_db)):
    scan_repo = ScanRepository(db)
    scan = scan_repo.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")
    
    if not scan.cbom_json:
        raise HTTPException(status_code=404, detail=f"CBOM not available for scan '{scan_id}'. Run or complete a scan first.")

    return scan.cbom_json

@router.post("/scans/{scan_id}/cbom/validate")
def validate_scan_cbom(scan_id: str, db: Session = Depends(get_db)):
    scan_repo = ScanRepository(db)
    scan = scan_repo.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")

    cbom = scan.cbom_json
    if not cbom:
        raise HTTPException(status_code=409, detail=f"CBOM not available for scan '{scan_id}'. Run or complete a scan first.")

    validator = CBOMValidator()
    is_valid = validator.validate(cbom)
    return {"scan_id": scan_id, "valid": is_valid, "specVersion": cbom.get("specVersion", "1.6")}

@router.get("/scans/{scan_id}/cbom/download")
def download_scan_cbom(scan_id: str, db: Session = Depends(get_db)):
    scan_repo = ScanRepository(db)
    scan = scan_repo.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")

    cbom = scan.cbom_json
    if not cbom:
        raise HTTPException(status_code=409, detail=f"CBOM not available for scan '{scan_id}'. Run or complete a scan first.")

    return JSONResponse(
        content=cbom,
        headers={"Content-Disposition": f'attachment; filename="cbom-{scan_id}.json"'}
    )

@router.get("/projects/{project_id}/cbom/download")
def download_project_cbom(project_id: str, db: Session = Depends(get_db)):
    proj_repo = ProjectRepository(db)
    scan_repo = ScanRepository(db)

    proj = proj_repo.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    scans = scan_repo.get_by_project(project_id)
    latest_scan = scans[0] if scans else None
    cbom = latest_scan.cbom_json if latest_scan else None
    
    if not cbom:
        raise HTTPException(status_code=409, detail=f"CBOM not available for project '{project_id}'. Please complete a scan first.")

    return JSONResponse(
        content=cbom,
        headers={"Content-Disposition": f'attachment; filename="cbom-{project_id}.json"'}
    )

@router.post("/projects/{project_id}/reports")
@router.get("/projects/{project_id}/reports/executive")
def create_project_report(project_id: str, db: Session = Depends(get_db)):
    proj_repo = ProjectRepository(db)
    asset_repo = AssetRepository(db)
    
    proj = proj_repo.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    assets = asset_repo.get_by_project(project_id)

    # Gather risk, Mosca, and recommendation results dynamically
    risk_service = RiskService(db)
    risk_summary = risk_service.get_project_risk_summary(project_id)
    
    mosca_engine = MoscaEngine()
    mosca_context = mosca_engine.evaluate_project_mosca(proj, assets)
    
    rec_service = RecommendationService(db)
    recs = rec_service.recommend_project(project_id)

    generator = ReportGenerator()
    report = generator.generate_project_report(
        project_name=proj.name,
        assets=assets,
        risk_summary=risk_summary,
        mosca_summary=mosca_context,
        recommendations=recs
    )
    report["report_id"] = f"rep-{project_id}"
    return report

@router.get("/projects/{project_id}/reports/executive/download")
def download_executive_report(project_id: str, db: Session = Depends(get_db)):
    report = create_project_report(project_id, db)
    html_content = report.get("report_html", "<h1>Report Generation Error</h1>")
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="executive-report-{project_id}.html"'}
    )

@router.get("/reports/{report_id}")
def get_report(report_id: str):
    return {"report_id": report_id, "status": "READY"}

@router.get("/reports/{report_id}/download")
def download_report(report_id: str):
    return {"report_id": report_id, "download_url": f"/api/v1/reports/{report_id}/file"}
