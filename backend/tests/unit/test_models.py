import pytest
from app.models.enums import RiskLevel, AssetType, CryptoPurpose, QuantumSafety

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_enums():
    assert RiskLevel.CRITICAL.value == "CRITICAL"
    assert AssetType.ALGORITHM.value == "ALGORITHM"
    assert CryptoPurpose.SIGNATURE.value == "SIGNATURE"
    assert QuantumSafety.QUANTUM_VULNERABLE.value == "QUANTUM_VULNERABLE"

def test_project_business_context_persistence(db_session):
    from app.repositories.project_repository import ProjectRepository
    from app.models.schemas import ProjectCreate
    repo = ProjectRepository(db_session)
    proj_create = ProjectCreate(
        name="Payments App",
        description="Core payments API",
        repository_url="https://github.com/org/payments.git",
        user_x_years=15,
        user_y_scenario="STANDARD",
        business_context={
            "data_sensitivity": 4,
            "operational_criticality": 5,
            "operational_cost": 4,
            "regulatory_impact": 5,
            "business_dependency": 4
        }
    )
    project = repo.create(proj_create)
    assert project.name == "Payments App"
    assert project.user_x_years == 15
    assert project.user_y_scenario == "STANDARD"
    assert project.business_context == {
        "data_sensitivity": 4,
        "operational_criticality": 5,
        "operational_cost": 4,
        "regulatory_impact": 5,
        "business_dependency": 4
    }
