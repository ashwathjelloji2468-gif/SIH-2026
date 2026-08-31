from fastapi import APIRouter
from app.knowledge.crypto_catalog import CRYPTO_CATALOG
from app.knowledge.pqc_catalog import PQC_CATALOG
from app.core.versioning import get_system_versions

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

@router.get("/catalog")
def get_crypto_catalog():
    return {"algorithms": CRYPTO_CATALOG, "pqc": PQC_CATALOG}

@router.get("/versions")
def get_knowledge_versions():
    return get_system_versions()
