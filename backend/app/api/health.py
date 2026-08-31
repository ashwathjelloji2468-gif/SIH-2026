from datetime import datetime, timezone
from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.core.versioning import get_system_versions

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    versions = get_system_versions()
    return HealthResponse(
        status="ok",
        version=versions["ecdat_software_version"],
        database="connected",
        versions=versions,
        timestamp=datetime.now(timezone.utc)
    )
