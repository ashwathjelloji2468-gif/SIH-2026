from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.repositories.finding_repository import FindingRepository
from app.discovery.coverage import CoverageEngine
from app.models.schemas import (
    CryptoAssetResponse, InventoryAssetResponse, EvidenceResponse,
    CoverageReportResponse, ReviewAssetRequest
)

router = APIRouter(tags=["Inventory"])

@router.get("/projects/{project_id}/inventory", response_model=List[InventoryAssetResponse])
def get_project_inventory(project_id: str, db: Session = Depends(get_db)):
    repo = AssetRepository(db)
    assets = repo.get_by_project(project_id)
    if not assets:
        return []

    from app.models.db_models import Project
    from app.engines.y_engine import YEngine
    from app.engines.z_engine import ZEngine
    from app.context.effective_context import resolve_effective_artifact_context

    project = db.query(Project).filter(Project.id == project_id).first() if db else None

    user_y_scen = getattr(project, "user_y_scenario", None) if project else None
    y_res = YEngine().evaluate_y(user_scenario=user_y_scen)

    eff_y = float(y_res["value"])
    eff_y_scen = str(y_res["scenario"])

    z_engine = ZEngine()
    results = []
    for asset in assets:
        eff_ctx = resolve_effective_artifact_context(asset, project, db)

        comp_dict = {
            "id": asset.id,
            "algorithm_name": asset.algorithm_name,
            "primitive": asset.algorithm_name,
            "purpose": asset.purpose.value if hasattr(asset.purpose, "value") else str(asset.purpose),
            "asset_type": asset.asset_type.value if hasattr(asset.asset_type, "value") else str(asset.asset_type),
            "location": asset.location,
            "key_size": getattr(asset, "key_size", None)
        }
        z_res = z_engine.evaluate_component(comp_dict)

        asset_dto = CryptoAssetResponse.model_validate(asset).model_dump()
        asset_dto.update({
            "effective_x_years": eff_ctx["x_years"],
            "effective_data_sensitivity": eff_ctx["data_sensitivity"],
            "effective_business_criticality": eff_ctx["business_criticality"],
            "effective_regulatory_impact": eff_ctx["regulatory_impact"],
            "effective_financial_impact": eff_ctx["financial_impact"],
            "effective_operational_impact": eff_ctx["operational_impact"],
            "effective_exposure": eff_ctx["exposure"],
            "effective_context_sources": eff_ctx["sources"],
            "effective_y_years": eff_y,
            "effective_y_scenario": eff_y_scen,
            "effective_z_value": z_res.get("z_value"),
            "effective_z_planning_horizon_years": z_res.get("z_planning_horizon_years"),
            "effective_z_target_year": z_res.get("z_target_year"),
            "xyz_source": "CANONICAL_PROJECT_CONTEXT"
        })
        results.append(asset_dto)

    return results

@router.get("/projects/{project_id}/coverage", response_model=CoverageReportResponse)
def get_project_coverage(project_id: str, db: Session = Depends(get_db)):
    repo = AssetRepository(db)
    assets = repo.get_by_project(project_id)
    engine = CoverageEngine()
    return engine.calculate_project_coverage(project_id, assets)

@router.get("/projects/{project_id}/unknowns", response_model=List[CryptoAssetResponse])
def get_project_unknowns(project_id: str, db: Session = Depends(get_db)):
    repo = AssetRepository(db)
    return repo.get_unknowns_by_project(project_id)

@router.post("/assets/{asset_id}/review", response_model=CryptoAssetResponse)
def review_unknown_asset(asset_id: str, req: ReviewAssetRequest, db: Session = Depends(get_db)):
    repo = AssetRepository(db)
    asset = repo.review_asset(asset_id, algorithm_name=req.algorithm_name, purpose=req.purpose, action=req.action)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.get("/assets/{asset_id}", response_model=CryptoAssetResponse)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    repo = AssetRepository(db)
    asset = repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.get("/assets/{asset_id}/evidence", response_model=List[EvidenceResponse])
def get_asset_evidence(asset_id: str, db: Session = Depends(get_db)):
    repo = FindingRepository(db)
    return repo.get_by_asset(asset_id)

@router.get("/assets/{asset_id}/history")
def get_asset_history(asset_id: str, db: Session = Depends(get_db)):
    repo = AssetRepository(db)
    asset = repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"asset_id": asset_id, "history": [{"timestamp": asset.created_at, "event": "Asset Discovered"}]}
