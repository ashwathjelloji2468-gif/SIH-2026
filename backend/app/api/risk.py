from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.risk.risk_engine import RiskEngine
from app.models.schemas import RiskAssessRequest, RiskAssessmentResponse

router = APIRouter(tags=["Risk"])

@router.post("/projects/{project_id}/risk/assess", response_model=List[Dict[str, Any]])
def assess_project_risk(project_id: str, req: RiskAssessRequest, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    assets = asset_repo.get_by_project(project_id)
    
    engine = RiskEngine()
    results = []
    
    for asset in assets:
        risk = engine.evaluate_asset_risk(
            algorithm_name=asset.algorithm_name,
            quantum_safety=asset.quantum_safety,
            data_sensitivity=req.data_sensitivity_score or 70.0,
            business_criticality=req.business_criticality_score or 80.0,
            quantum_threat_horizon_year=req.quantum_threat_horizon_year or 2033
        )
        risk["asset_id"] = asset.id
        risk["asset_name"] = asset.name
        results.append(risk)

    return results

@router.get("/projects/{project_id}/risk/summary")
def get_risk_summary(project_id: str, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    assets = asset_repo.get_by_project(project_id)
    engine = RiskEngine()

    high_risk_count = 0
    total_score = 0.0

    for asset in assets:
        risk = engine.evaluate_asset_risk(asset.algorithm_name, asset.quantum_safety)
        total_score += risk["risk_score"]
        if risk["risk_score"] >= 60.0:
            high_risk_count += 1

    avg_score = round(total_score / max(1, len(assets)), 1)
    return {
        "project_id": project_id,
        "total_assets": len(assets),
        "high_or_critical_risk_assets": high_risk_count,
        "average_risk_score": avg_score
    }

@router.get("/assets/{asset_id}/risk")
def get_asset_risk(asset_id: str, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    asset = asset_repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    engine = RiskEngine()
    return engine.evaluate_asset_risk(asset.algorithm_name, asset.quantum_safety)

@router.get("/assets/{asset_id}/risk/explanation")
def get_asset_risk_explanation(asset_id: str, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    asset = asset_repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    engine = RiskEngine()
    risk = engine.evaluate_asset_risk(asset.algorithm_name, asset.quantum_safety)
    return {"asset_id": asset_id, "explanation": risk["explanation"]}
