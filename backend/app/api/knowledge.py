from typing import Optional
from fastapi import APIRouter, Query
from app.knowledge.crypto_catalog import CRYPTO_CATALOG, evaluate_quantum_assessment
from app.knowledge.pqc_catalog import PQC_CATALOG
from app.models.enums import CryptoPurpose
from app.core.versioning import get_system_versions

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

@router.get("/catalog")
def get_crypto_catalog():
    return {"algorithms": CRYPTO_CATALOG, "pqc": PQC_CATALOG}

@router.get("/evaluate")
def evaluate_algorithm(
    algorithm_name: str = Query(..., description="Name of cryptographic algorithm (e.g. RSA, AES, SHA-256)"),
    key_size: Optional[int] = Query(None, description="Key size in bits"),
    purpose: Optional[CryptoPurpose] = Query(None, description="Cryptographic purpose")
):
    return evaluate_quantum_assessment(algorithm_name=algorithm_name, key_size=key_size, purpose=purpose)

@router.get("/versions")
def get_knowledge_versions():
    return get_system_versions()

