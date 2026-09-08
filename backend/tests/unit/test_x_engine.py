import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.db_models import Project, Scan
from app.config.domain_baselines import DOMAIN_X_BASELINES, DEFAULT_CONFIDENTIALITY_HORIZON_YEARS
from app.services.domain_classifier import DomainClassifier
from app.engines.x_engine import XEngine
from app.repositories.project_repository import ProjectRepository

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_1_user_provided_x_overrides_everything():
    engine = XEngine()
    result = engine.evaluate_x(
        user_x_years=10,
        user_domain="government_defense",
        project_name="Military Encryption System"
    )

    assert result["value"] == 10
    assert result["source"] == "USER"
    assert result["confidence"] == "HIGH"
    assert result["userX"] == 10
    assert result["estimatedDomainX"] == 50
    assert result["overrideAvailable"] is True
    assert "Organization-selected confidentiality horizon of 10 years is active" in result["explanation"]

def test_2_domain_baseline_when_no_user_x():
    engine = XEngine()
    result = engine.evaluate_x(
        user_domain="healthcare",
        project_name="Patient Health Record EHR"
    )

    assert result["value"] == 30
    assert result["source"] == "DOMAIN_BASELINE"
    assert result["domain"] == "healthcare"
    assert result["userX"] is None
    assert result["estimatedDomainX"] == 30

def test_3_automatic_domain_classifier_high_confidence():
    classifier = DomainClassifier()
    res = classifier.classify_repository(
        project_name="Demo Banking System",
        description="Core financial ledger and payment gateway",
        repository_url="https://github.com/bank/ledger.git"
    )

    assert res["domain"] == "banking_finance"
    assert res["baseline_x_years"] == 15
    assert res["confidence"] in ("HIGH", "MEDIUM")

def test_4_system_default_fallback_unclassified():
    engine = XEngine()
    result = engine.evaluate_x(
        project_name="foo",
        description="bar"
    )


    assert result["value"] == 20
    assert result["source"] == "SYSTEM_DEFAULT"
    assert result["domain"] == "unclassified"
    assert result["confidence"] == "LOW"
    assert "conservative 20-year confidentiality planning horizon" in result["explanation"]

def test_5_folder_level_context_override():
    engine = XEngine()
    folder_contexts = {
        "services/payment": {
            "user_x_years": 12,
            "notes": "PCI-DSS compliance window"
        }
    }

    result = engine.evaluate_x(
        user_x_years=30,  # Repo-level X = 30
        folder_path="services/payment",
        folder_contexts=folder_contexts
    )

    assert result["value"] == 12
    assert result["source"] == "USER"
    assert result["contextLevel"] == "FOLDER"
    assert result["userX"] == 12
    assert "PCI-DSS compliance window" in result["explanation"]

def test_6_project_repository_x_context_persistence(db_session):
    repo = ProjectRepository(db_session)
    project = repo.create(type("Obj", (), {
        "name": "Fintech Core Bank",
        "description": "Payment backend",
        "repository_url": None
    }))

    updated = repo.update_x_context(
        project_id=project.id,
        user_x_years=15,
        user_domain="banking_finance",
        folder_contexts={"services/auth": {"user_x_years": 10, "notes": "Session tokens"}}
    )

    assert updated.user_x_years == 15
    assert updated.user_domain == "banking_finance"
    assert updated.folder_contexts["services/auth"]["user_x_years"] == 10
