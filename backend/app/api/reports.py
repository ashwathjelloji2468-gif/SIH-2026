from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.scan_repository import ScanRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.project_repository import ProjectRepository
from app.cbom.validator import CBOMValidator
from app.reports.report_generator import ReportGenerator
from app.risk.service import RiskService
from app.engines.mosca_engine import MoscaEngine
from app.recommend.service import RecommendationService
from app.services.business_criticality_service import BusinessCriticalityService
from app.graph.blast_radius_engine import BlastRadiusEngine
from app.models.db_models import ValidationRun, RiskAssessment

router = APIRouter(tags=["Reports & CBOM"])


def resolve_and_validate_project_and_scan(db: Session, project_id: str, scan_id: Optional[str] = None):
    """
    Validates project and scan ownership strictly.
    Returns (project, scan). Raises HTTP 404 / 400 if invalid or mismatched.
    """
    proj_repo = ProjectRepository(db)
    scan_repo = ScanRepository(db)

    project = proj_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    scan = None
    if scan_id:
        scan = scan_repo.get(scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")
        if scan.project_id != project_id:
            raise HTTPException(status_code=400, detail=f"Scan '{scan_id}' does not belong to project '{project_id}'")
    else:
        scans = scan_repo.get_by_project(project_id)
        # Prefer completed scan if available
        completed_scans = [s for s in scans if str(getattr(s, "status", "")).upper() == "COMPLETED"]
        scan = completed_scans[0] if completed_scans else (scans[0] if scans else None)

    return project, scan


# ============================================================================
# 1. CANONICAL CBOM JSON ENDPOINTS
# ============================================================================

@router.get("/scans/{scan_id}/cbom")
def get_scan_cbom(scan_id: str, db: Session = Depends(get_db)):
    scan_repo = ScanRepository(db)
    scan = scan_repo.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")
    
    if not scan.cbom_json:
        raise HTTPException(status_code=404, detail=f"CBOM_NOT_AVAILABLE: CBOM not available for scan '{scan_id}'. Run or complete a scan first.")

    return scan.cbom_json


@router.post("/scans/{scan_id}/cbom/validate")
def validate_scan_cbom(scan_id: str, db: Session = Depends(get_db)):
    scan_repo = ScanRepository(db)
    scan = scan_repo.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")

    cbom = scan.cbom_json
    if not cbom:
        raise HTTPException(status_code=409, detail=f"CBOM_NOT_AVAILABLE: CBOM not available for scan '{scan_id}'. Run or complete a scan first.")

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
        raise HTTPException(status_code=409, detail=f"CBOM_NOT_AVAILABLE: CBOM not available for scan '{scan_id}'. Run or complete a scan first.")

    return JSONResponse(
        content=cbom,
        headers={"Content-Disposition": f'attachment; filename="cbom-{scan_id}.json"'}
    )


@router.get("/projects/{project_id}/cbom/download")
def download_project_cbom(project_id: str, scan_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    project, scan = resolve_and_validate_project_and_scan(db, project_id=project_id, scan_id=scan_id)
    
    cbom = scan.cbom_json if scan else None
    if not cbom:
        raise HTTPException(status_code=409, detail=f"CBOM_NOT_AVAILABLE: CBOM not available for project '{project_id}'. Please complete a scan first.")

    return JSONResponse(
        content=cbom,
        headers={"Content-Disposition": f'attachment; filename="cbom-{project_id}.json"'}
    )


# ============================================================================
# 2. CANONICAL CBOM PDF ENDPOINTS
# ============================================================================

@router.get("/scans/{scan_id}/cbom/pdf")
def get_scan_cbom_pdf(scan_id: str, db: Session = Depends(get_db)):
    scan_repo = ScanRepository(db)
    scan = scan_repo.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")

    cbom = scan.cbom_json
    if not cbom:
        raise HTTPException(status_code=409, detail=f"CBOM_NOT_AVAILABLE: CBOM not available for scan '{scan_id}'. Run or complete a scan first.")

    proj_name = scan.project.name if scan.project else "Project"
    scan_time = scan.created_at.isoformat() if scan.created_at else None

    generator = ReportGenerator()
    return generator.generate_cbom_pdf(
        cbom_json=cbom,
        project_name=proj_name,
        project_id=scan.project_id,
        scan_id=scan.id,
        scan_timestamp=scan_time
    )


@router.get("/scans/{scan_id}/cbom/pdf/download")
def download_scan_cbom_pdf(scan_id: str, db: Session = Depends(get_db)):
    pdf_report = get_scan_cbom_pdf(scan_id=scan_id, db=db)
    html_content = pdf_report.get("report_html", "<h1>CBOM PDF Generation Error</h1>")
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="cbom-{scan_id}.html"'}
    )


@router.get("/projects/{project_id}/cbom/pdf/download")
def download_project_cbom_pdf(project_id: str, scan_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    project, scan = resolve_and_validate_project_and_scan(db, project_id=project_id, scan_id=scan_id)
    if not scan or not scan.cbom_json:
        raise HTTPException(status_code=409, detail=f"CBOM_NOT_AVAILABLE: CBOM not available for project '{project_id}'. Please complete a scan first.")

    scan_time = scan.created_at.isoformat() if scan.created_at else None
    generator = ReportGenerator()
    pdf_report = generator.generate_cbom_pdf(
        cbom_json=scan.cbom_json,
        project_name=project.name,
        project_id=project.id,
        scan_id=scan.id,
        scan_timestamp=scan_time
    )
    html_content = pdf_report.get("report_html", "<h1>CBOM PDF Generation Error</h1>")
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="cbom-{scan.id}.html"'}
    )


# ============================================================================
# 3. AUTHORITATIVE RISK REPORT ENDPOINTS
# ============================================================================

@router.get("/projects/{project_id}/reports/risk")
@router.get("/scans/{scan_id}/reports/risk")
def get_risk_report(
    project_id: Optional[str] = None,
    scan_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    target_project_id = project_id
    if not target_project_id and scan_id:
        scan_obj = ScanRepository(db).get(scan_id)
        if scan_obj:
            target_project_id = scan_obj.project_id

    if not target_project_id:
        raise HTTPException(status_code=400, detail="project_id or scan_id required to generate Risk Report.")

    project, scan = resolve_and_validate_project_and_scan(db, project_id=target_project_id, scan_id=scan_id)

    asset_repo = AssetRepository(db)
    if scan:
        assets = asset_repo.get_by_scan(scan.id)
    else:
        assets = asset_repo.get_by_project(project.id)

    risk_service = RiskService(db)
    risk_summary = risk_service.get_project_risk_summary(project.id)

    mosca_engine = MoscaEngine()
    mosca_summary = mosca_engine.evaluate_project_mosca(project, assets)

    crit_service = BusinessCriticalityService(db)
    b_context = crit_service.get_project_business_criticality(project.id)

    # Priority 6 Blast Radius
    blast_engine = BlastRadiusEngine()
    top_br = blast_engine.get_top_blast_radii_for_project(project.id, db)
    blast_radii_list = top_br.get("top_blast_radii", [])

    # Fetch actual RiskAssessment DB objects
    asset_ids = [a.id for a in assets]
    ra_objs = db.query(RiskAssessment).filter(RiskAssessment.asset_id.in_(asset_ids)).all() if asset_ids else []
    ra_dicts = [
        {
            "asset_id": ra.asset_id,
            "risk_score": ra.risk_score,
            "risk_level": ra.risk_level.value if hasattr(ra.risk_level, "value") else str(ra.risk_level),
            "explanation": ra.explanation
        } for ra in ra_objs
    ]

    scan_time = scan.created_at.isoformat() if (scan and scan.created_at) else None

    generator = ReportGenerator()
    report = generator.generate_risk_report(
        project_name=project.name,
        assets=assets,
        project_id=project.id,
        scan_id=scan.id if scan else None,
        scan_timestamp=scan_time,
        risk_assessments=ra_dicts,
        risk_summary=risk_summary,
        mosca_summary=mosca_summary,
        business_criticality=b_context,
        blast_radius_results=blast_radii_list
    )
    return report


@router.get("/projects/{project_id}/reports/risk/download")
def download_risk_report(project_id: str, scan_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    report = get_risk_report(project_id=project_id, scan_id=scan_id, db=db)
    html_content = report.get("report_html", "<h1>Risk Report Error</h1>")
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="risk-report-{project_id}.html"'}
    )


# ============================================================================
# 4. AUTHORITATIVE EXECUTIVE REPORT ENDPOINTS
# ============================================================================

@router.post("/projects/{project_id}/reports")
@router.get("/projects/{project_id}/reports/executive")
def create_project_report(project_id: str, scan_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    project, scan = resolve_and_validate_project_and_scan(db, project_id=project_id, scan_id=scan_id)

    asset_repo = AssetRepository(db)
    if scan:
        assets = asset_repo.get_by_scan(scan.id)
    else:
        assets = asset_repo.get_by_project(project_id)

    # Gather actual risk, Mosca, business criticality, recommendations, blast radius, validation
    risk_service = RiskService(db)
    risk_summary = risk_service.get_project_risk_summary(project_id)

    mosca_engine = MoscaEngine()
    mosca_summary = mosca_engine.evaluate_project_mosca(project, assets)

    crit_service = BusinessCriticalityService(db)
    b_context = crit_service.get_project_business_criticality(project_id)

    rec_service = RecommendationService(db)
    recs = rec_service.recommend_project(project_id)

    blast_engine = BlastRadiusEngine()
    br_summary = blast_engine.get_top_blast_radii_for_project(project_id, db)

    # Last validation run for project
    last_val = db.query(ValidationRun).filter(ValidationRun.project_id == project_id).order_by(ValidationRun.created_at.desc()).first()
    val_status = {
        "build_passed": last_val.build_passed if last_val else False,
        "unit_tests_passed": last_val.unit_tests_passed if last_val else False,
        "crypto_tests_passed": last_val.crypto_tests_passed if last_val else False
    } if last_val else None

    scan_time = scan.created_at.isoformat() if (scan and scan.created_at) else None

    generator = ReportGenerator()
    report = generator.generate_project_report(
        project_name=project.name,
        assets=assets,
        project_id=project.id,
        scan_id=scan.id if scan else None,
        scan_timestamp=scan_time,
        repository_url=project.repository_url,
        risk_summary=risk_summary,
        mosca_summary=mosca_summary,
        recommendations=recs,
        business_criticality=b_context,
        blast_radius_summary=br_summary,
        validation_status=val_status
    )
    report["report_id"] = f"rep-{project_id}"
    return report


@router.get("/projects/{project_id}/reports/executive/download")
def download_executive_report(project_id: str, scan_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    report = create_project_report(project_id=project_id, scan_id=scan_id, db=db)
    html_content = report.get("report_html", "<h1>Executive Report Generation Error</h1>")
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
