from datetime import datetime, timezone
from fastapi import APIRouter
from app.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        database="connected",
        timestamp=datetime.now(timezone.utc)
    )
