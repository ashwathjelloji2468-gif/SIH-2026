from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.recommend.engine import RecommendationEngine
from app.knowledge.pqc_catalog import PQC_CATALOG
from app.knowledge.standard_registry import STANDARD_REGISTRY

router = APIRouter(tags=["Recommendations"])

@router.get("/assets/{asset_id}/recommendations", response_model=List[Dict[str, Any]])
def get_asset_recommendations(asset_id: str, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    asset = asset_repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    engine = RecommendationEngine()
    return engine.evaluate_recommendations(asset)

@router.post("/assets/{asset_id}/recommendations/evaluate")
def evaluate_asset_recommendation(asset_id: str, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    asset = asset_repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    engine = RecommendationEngine()
    return {"asset_id": asset_id, "recommendations": engine.evaluate_recommendations(asset)}

@router.get("/knowledge/pqc")
def get_pqc_knowledge():
    return PQC_CATALOG

@router.get("/knowledge/standards")
def get_standards_knowledge():
    return STANDARD_REGISTRY
