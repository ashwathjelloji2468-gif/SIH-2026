import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.db_models import Project
from app.config.migration_scenarios import MIGRATION_SCENARIOS, DEFAULT_Y_SCENARIO, DEFAULT_Y_YEARS
from app.engines.y_engine import YEngine
from app.repositories.project_repository import ProjectRepository

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_1_default_mvp_y_behavior():
    engine = YEngine()
    result = engine.evaluate_y()

    assert result["value"] == 10
    assert result["unit"] == "years"
    assert result["scenario"] == "STANDARD"
    assert result["source"] == "SYSTEM_DEFAULT"
    assert "standardized 10-year migration planning assumption" in result["explanation"]

def test_2_fast_migration_scenario():
    engine = YEngine()
    result = engine.evaluate_y(user_scenario="FAST")

    assert result["value"] == 5
    assert result["scenario"] == "FAST"
    assert result["source"] == "USER_SELECTED"
    assert result["scenarioTitle"] == "Fast / Simple Migration"

def test_3_complex_migration_scenario():
    engine = YEngine()
    result = engine.evaluate_y(user_scenario="COMPLEX")

    assert result["value"] == 15
    assert result["scenario"] == "COMPLEX"
    assert result["source"] == "USER_SELECTED"

def test_4_legacy_heavy_migration_scenario():
    engine = YEngine()
    result = engine.evaluate_y(user_scenario="LEGACY_HEAVY")

    assert result["value"] == 20
    assert result["scenario"] == "LEGACY_HEAVY"
    assert result["source"] == "USER_SELECTED"

def test_5_project_repository_y_context_persistence(db_session):
    repo = ProjectRepository(db_session)
    project = repo.create(type("Obj", (), {
        "name": "Legacy Core Platform",
        "description": "Mainframe banking portal",
        "repository_url": None
    }))

    updated = repo.update_y_context(
        project_id=project.id,
        user_y_scenario="LEGACY_HEAVY"
    )

    assert updated.user_y_scenario == "LEGACY_HEAVY"

    engine = YEngine()
    result = engine.evaluate_y(user_scenario=updated.user_y_scenario)
    assert result["value"] == 20
    assert result["source"] == "USER_SELECTED"
