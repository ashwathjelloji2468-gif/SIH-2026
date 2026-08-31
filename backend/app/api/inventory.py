from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.repositories.finding_repository import FindingRepository
from app.discovery.coverage import CoverageEngine
from app.models.schemas import CryptoAssetResponse, EvidenceResponse, CoverageReportResponse, ReviewAssetRequest

router = APIRouter(tags=["Inventory"])

@router.get("/projects/{project_id}/inventory", response_model=List[CryptoAssetResponse])
def get_project_inventory(project_id: str, db: Session = Depends(get_db)):
    repo = AssetRepository(db)
    return repo.get_by_project(project_id)

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
