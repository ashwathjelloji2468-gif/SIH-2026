from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.project_repository import ProjectRepository
from app.repositories.asset_repository import AssetRepository
from app.qars.service import evaluate_artifact_qars
from app.qars.schemas import QARSProjectSummarySchema, QARSResponseSchema
from app.qars.models import QARSValidationError, QARSRuntimeResult

router = APIRouter(tags=["QARS"])


@router.get("/projects/{project_id}/qars", response_model=QARSProjectSummarySchema)
def get_project_qars(
    project_id: str,
    scan_id: Optional[str] = None,
    latest_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Evaluates artifact-level QARS across all assets in a project scope and returns structured summary metrics.
    """
    proj_repo = ProjectRepository(db)
    project = proj_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    asset_repo = AssetRepository(db)
    assets = asset_repo.get_by_project(project_id, scan_id=scan_id, latest_only=latest_only)

    precomputed_bc = None
    if project and db:
        try:
            from app.services.business_criticality_service import BusinessCriticalityService
            srv = BusinessCriticalityService(db)
            precomputed_bc = srv.get_project_business_criticality(project.id)
        except Exception:
            precomputed_bc = None

    from app.qars.models import QARSRuntimeResult

    evaluated_assets = []
    for asset in assets:
        extra = dict(getattr(asset, "extra_metadata", {}) or {}) if hasattr(asset, "extra_metadata") else (asset.get("extra_metadata", {}) if isinstance(asset, dict) else {})
        cached_qars = extra.get("qars_result")
        if cached_qars and isinstance(cached_qars, dict) and "level" in cached_qars:
            try:
                res = QARSRuntimeResult.model_validate(cached_qars)
                evaluated_assets.append(res)
                continue
            except Exception:
                pass

        try:
            res = evaluate_artifact_qars(asset, project, db, precomputed_business_context=precomputed_bc)
            evaluated_assets.append(res)
        except QARSValidationError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    asset_count = len(evaluated_assets)
    project_name = getattr(project, "name", "Project") or "Project"

    if asset_count == 0:
        summary: Dict[str, Any] = {
            "qars_average": None,
            "qars_max": None,
            "qars_min": None,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "unconfigured_count": 0,
        }
    else:
        valid_scores = [a.final_score for a in evaluated_assets if a.final_score is not None]
        summary = {
            "qars_average": round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else None,
            "qars_max": round(max(valid_scores), 2) if valid_scores else None,
            "qars_min": round(min(valid_scores), 2) if valid_scores else None,
            "critical_count": sum(
                1 for a in evaluated_assets
                if getattr(a.level, "value", str(a.level)) == "CRITICAL"
            ),
            "high_count": sum(
                1 for a in evaluated_assets
                if getattr(a.level, "value", str(a.level)) == "HIGH"
            ),
            "medium_count": sum(
                1 for a in evaluated_assets
                if getattr(a.level, "value", str(a.level)) == "MEDIUM"
            ),
            "low_count": sum(
                1 for a in evaluated_assets
                if getattr(a.level, "value", str(a.level)) == "LOW"
            ),
            "unconfigured_count": sum(
                1 for a in evaluated_assets
                if (
                    a.final_score is None
                    or getattr(a.level, "value", str(a.level)) == "UNCONFIGURED"
                )
            ),
        }

    return QARSProjectSummarySchema(
        project_id=project_id,
        project_name=project_name,
        asset_count=asset_count,
        summary=summary,
        assets=evaluated_assets,
    )


@router.get("/projects/{project_id}/qars/assets/{asset_id}", response_model=QARSResponseSchema)
def get_asset_qars(project_id: str, asset_id: str, db: Session = Depends(get_db)):
    """
    Evaluates QARS for a specific asset within a project. Returns HTTP 404 if asset belongs to another project.
    """
    proj_repo = ProjectRepository(db)
    project = proj_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    asset_repo = AssetRepository(db)
    asset = asset_repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")

    # Confirm asset belongs to requested project
    asset_proj_id = (
        getattr(asset, "project_id", None)
        or (asset.scan.project_id if hasattr(asset, "scan") and asset.scan else None)
    )
    if str(asset_proj_id) != str(project_id):
        raise HTTPException(
            status_code=404,
            detail=f"Asset '{asset_id}' not found in project '{project_id}'"
        )

    try:
        extra = dict(getattr(asset, "extra_metadata", {}) or {}) if hasattr(asset, "extra_metadata") else (asset.get("extra_metadata", {}) if isinstance(asset, dict) else {})
        cached_qars = extra.get("qars_result")
        if cached_qars and isinstance(cached_qars, dict) and "level" in cached_qars:
            try:
                qars_result = QARSRuntimeResult.model_validate(cached_qars)
            except Exception:
                qars_result = evaluate_artifact_qars(asset, project, db)
        else:
            qars_result = evaluate_artifact_qars(asset, project, db)
    except QARSValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return QARSResponseSchema(
        status="SUCCESS",
        data=qars_result,
        message="Asset QARS evaluation completed successfully."
    )
