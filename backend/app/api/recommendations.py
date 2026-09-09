from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.recommend.engine import RecommendationEngine
from app.recommend.service import RecommendationService
from app.knowledge.pqc_catalog import PQC_CATALOG
from app.knowledge.standard_registry import STANDARD_REGISTRY

router = APIRouter(tags=["Recommendations"])

@router.get("/assets/{asset_id}/recommendations", response_model=List[Dict[str, Any]])
def get_asset_recommendations(asset_id: str, db: Session = Depends(get_db)):
    service = RecommendationService(db)
    try:
        rec = service.recommend_asset(asset_id)
        return [rec]
    except Exception:
        asset_repo = AssetRepository(db)
        asset = asset_repo.get(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        engine = RecommendationEngine()
        return engine.evaluate_recommendations(asset)

@router.post("/assets/{asset_id}/recommendations/evaluate")
def evaluate_asset_recommendation(asset_id: str, db: Session = Depends(get_db)):
    service = RecommendationService(db)
    try:
        rec = service.recommend_asset(asset_id, force_regeneration=True)
        return {"asset_id": asset_id, "recommendations": [rec]}
    except Exception:
        asset_repo = AssetRepository(db)
        asset = asset_repo.get(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        engine = RecommendationEngine()
        return {"asset_id": asset_id, "recommendations": engine.evaluate_recommendations(asset)}

@router.get("/projects/{project_id}/recommendations", response_model=List[Dict[str, Any]])
def get_project_recommendations(project_id: str, db: Session = Depends(get_db)):
    """Retrieve full real PQC recommendations for all cryptographic assets in a project."""
    service = RecommendationService(db)
    return service.recommend_project(project_id)

@router.get("/projects/{project_id}/recommendations/summary")
def get_project_recommendations_summary(project_id: str, db: Session = Depends(get_db)):
    """Retrieve aggregate recommendation metrics and detailed recommendation list for a project."""
    service = RecommendationService(db)
    return service.get_project_recommendation_summary(project_id)

@router.get("/knowledge/pqc")
def get_pqc_knowledge():
    return PQC_CATALOG

@router.get("/knowledge/standards")
def get_standards_knowledge():
    return STANDARD_REGISTRY
