from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.models.schemas import CryptoAssetResponse

router = APIRouter(tags=["Findings"])

@router.get("/projects/{project_id}/findings", response_model=List[CryptoAssetResponse])
def get_project_findings(project_id: str, db: Session = Depends(get_db)):
    repo = AssetRepository(db)
    return repo.get_by_project(project_id)
