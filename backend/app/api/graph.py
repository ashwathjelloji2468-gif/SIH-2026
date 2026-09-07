from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.graph.graph_builder import build_project_graph, GraphBuilder
from app.graph.impact import ImpactAnalyzer

router = APIRouter(tags=["Graph & Impact"])

@router.get("/graph")
def get_overall_graph(project_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    if project_id:
        assets = asset_repo.get_by_project(project_id)
    else:
        # Load all assets if no project_id specified
        assets = db.query(AssetRepository(db).db.query(AssetRepository(db).get.__self__.db.models.db_models.CryptoAsset).first().__class__).all() if hasattr(asset_repo, "db") else []
        if not assets:
            assets = asset_repo.get_by_project("default_project")

    risk_repo = RiskRepository(db)
    rec_repo = RecommendationRepository(db)
    
    risks = [risk_repo.get_latest_for_asset(a.id) for a in assets if risk_repo.get_latest_for_asset(a.id)]
    recs = [rec_repo.get_latest_for_asset(a.id) for a in assets if rec_repo.get_latest_for_asset(a.id)]

    graph = build_project_graph(assets=assets, risks=risks, recommendations=recs)
    return graph.to_dict()

@router.get("/graph/{asset_id}")
def get_asset_graph(asset_id: str, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    asset = asset_repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Crypto asset '{asset_id}' not found")

    risk_repo = RiskRepository(db)
    rec_repo = RecommendationRepository(db)

    ra = risk_repo.get_latest_for_asset(asset_id)
    rec = rec_repo.get_latest_for_asset(asset_id)

    all_assets = asset_repo.get_by_project(asset.scan.project_id) if asset.scan else [asset]
    graph = build_project_graph(assets=all_assets, risks=[ra] if ra else [], recommendations=[rec] if rec else [])
    
    # Return full graph dictionary
    return graph.to_dict()

@router.get("/graph/impact/{asset_id}")
def get_graph_impact_analysis(asset_id: str, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    asset = asset_repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Crypto asset '{asset_id}' not found")

    risk_repo = RiskRepository(db)
    rec_repo = RecommendationRepository(db)

    ra = risk_repo.get_latest_for_asset(asset_id)
    rec = rec_repo.get_latest_for_asset(asset_id)

    all_assets = asset_repo.get_by_project(asset.scan.project_id) if asset.scan else [asset]

    analyzer = ImpactAnalyzer()
    return analyzer.analyze_asset_impact(asset, all_assets, ra, rec)

@router.get("/projects/{project_id}/graph")
def get_project_graph(project_id: str, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    assets = asset_repo.get_by_project(project_id)
    risk_repo = RiskRepository(db)
    rec_repo = RecommendationRepository(db)

    risks = [risk_repo.get_latest_for_asset(a.id) for a in assets if risk_repo.get_latest_for_asset(a.id)]
    recs = [rec_repo.get_latest_for_asset(a.id) for a in assets if rec_repo.get_latest_for_asset(a.id)]

    graph = build_project_graph(assets=assets, risks=risks, recommendations=recs)
    return graph.to_dict()

@router.get("/assets/{asset_id}/impact")
def get_asset_impact(asset_id: str, db: Session = Depends(get_db)):
    return get_graph_impact_analysis(asset_id, db)

@router.post("/assets/{asset_id}/impact/simulate")
def simulate_asset_impact(asset_id: str, db: Session = Depends(get_db)):
    return get_graph_impact_analysis(asset_id, db)
