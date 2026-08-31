from sqlalchemy.orm import Session
from app.models.db_models import Algorithm, Standard, PQCCandidate, DataClassification, BusinessCriticality
from app.knowledge.crypto_catalog import CRYPTO_CATALOG
from app.knowledge.pqc_catalog import PQC_CATALOG
from app.knowledge.standard_registry import STANDARD_REGISTRY
from app.core.logging import logger

def init_knowledge_base(db: Session):
    """Populates reference database tables with NIST PQC and legacy cryptographic knowledge on startup."""
    try:
        # Load Algorithms
        for alg_name, info in CRYPTO_CATALOG.items():
            existing = db.query(Algorithm).filter(Algorithm.name == alg_name).first()
            if not existing:
                db.add(Algorithm(
                    name=alg_name,
                    family=info["family"],
                    is_quantum_vulnerable=info["quantum_vulnerable"],
                    standard_status=info["status"]
                ))

        # Load Standards
        for std_code, info in STANDARD_REGISTRY.items():
            existing = db.query(Standard).filter(Standard.code == std_code).first()
            if not existing:
                db.add(Standard(
                    code=std_code,
                    name=info["title"],
                    status=info["status"],
                    description=f"Organization: {info['organization']}, Year: {info['release_year']}"
                ))

        # Load PQC Candidates
        for pqc_name, info in PQC_CATALOG.items():
            existing = db.query(PQCCandidate).filter(PQCCandidate.name == pqc_name).first()
            if not existing:
                db.add(PQCCandidate(
                    name=pqc_name,
                    standard_code=info["standard_code"],
                    purpose=info["purposes"][0],
                    status=info["status"],
                    key_size_notes=info["key_size_notes"]
                ))

        # Load Default Data Classifications
        classifications = [
            ("PUBLIC", 10.0),
            ("INTERNAL", 30.0),
            ("CONFIDENTIAL", 70.0),
            ("RESTRICTED_SECRET", 100.0)
        ]
        for name, score in classifications:
            existing = db.query(DataClassification).filter(DataClassification.level_name == name).first()
            if not existing:
                db.add(DataClassification(level_name=name, sensitivity_score=score))

        # Load Default Business Criticalities
        criticalities = [
            ("LOW", 20.0),
            ("MEDIUM", 50.0),
            ("HIGH", 80.0),
            ("MISSION_CRITICAL", 100.0)
        ]
        for name, score in criticalities:
            existing = db.query(BusinessCriticality).filter(BusinessCriticality.level_name == name).first()
            if not existing:
                db.add(BusinessCriticality(level_name=name, criticality_score=score))

        db.commit()
        logger.info("Cryptographic Knowledge Base reference tables initialized successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to initialize Knowledge Base: {e}")
