import pytest
from app.core.database import SessionLocal
from app.models.db_models import Project, Scan, CryptoAsset, MigrationPlan, MigrationSimulation, ValidationRun, RiskAssessment
from app.models.enums import AssetType, CryptoPurpose, QuantumSafety, RiskLevel, SimulationStatus, ValidationStatus
from app.repositories.migration_repository import MigrationRepository
from app.repositories.migration_simulation_repository import MigrationSimulationRepository
from app.repositories.validation_repository import ValidationRepository
from app.repositories.risk_repository import RiskRepository
from app.migration.planner import MigrationPlanner
from app.risk.service import RiskService
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

def test_real_plan_simulation_validation_relational_integrity(db_session):

    # Setup test project & asset
    project = Project(name="Test Relational Integrity Project")
    db_session.add(project)
    db_session.commit()

    scan = Scan(project_id=project.id, target_path="/app", scan_type="AST", status="COMPLETED")

    db_session.add(scan)
    db_session.commit()

    asset = CryptoAsset(
        scan_id=scan.id,
        name="RSA Key Pair",
        algorithm_name="RSA-2048",
        asset_type=AssetType.ALGORITHM,
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        location="auth/jwt.py"
    )
    db_session.add(asset)
    db_session.commit()

    # Step 1: Create real MigrationPlan
    planner = MigrationPlanner()
    plan = planner.create_plan_for_project(
        db=db_session,
        project_id=project.id,
        plan_name="Relational Test Plan",
        assets=[asset]
    )

    assert plan.id is not None

    # Step 2: Create MigrationSimulation linked to real plan
    sim_repo = MigrationSimulationRepository(db_session)
    sim = sim_repo.create_simulation(
        asset_id=asset.id,
        project_id=project.id,
        migration_plan_id=plan.id,
        status=SimulationStatus.TRANSFORMED
    )

    assert sim.migration_plan_id == plan.id

    # Step 3: Create ValidationRun for simulation
    val_repo = ValidationRepository(db_session)
    val = val_repo.create_validation_run(
        simulation_id=sim.id,
        asset_id=asset.id,
        status=ValidationStatus.PASSED
    )

    # Invariant Verification
    assert val.plan_id == sim.migration_plan_id == plan.id
    assert not str(val.plan_id).startswith("plan-sim")

def test_standalone_simulation_validation_no_fake_plan_id(db_session):
    # Create standalone simulation without migration plan
    sim_repo = MigrationSimulationRepository(db_session)
    sim = sim_repo.create_simulation(
        asset_id="asset-standalone-123",
        project_id="proj-standalone-123",
        migration_plan_id=None,
        status=SimulationStatus.TRANSFORMED
    )

    assert sim.migration_plan_id is None

    # Create ValidationRun for standalone simulation
    val_repo = ValidationRepository(db_session)
    val = val_repo.create_validation_run(
        simulation_id=sim.id,
        asset_id="asset-standalone-123",
        status=ValidationStatus.PASSED
    )

    # Invariant Verification: No pseudo plan ID string manufactured!
    assert val.plan_id is None
    assert val.simulation_id == sim.id

def test_quantum_vulnerable_classification_vs_persisted_risk_assessment(db_session):
    project = Project(name="Classification Integrity Project")
    db_session.add(project)
    db_session.commit()

    scan = Scan(project_id=project.id, target_path="/app", scan_type="AST", status="COMPLETED")

    db_session.add(scan)
    db_session.commit()

    # Asset 1: Vulnerable (ECDSA)
    a1 = CryptoAsset(
        scan_id=scan.id,
        name="ECDSA Key",
        algorithm_name="ECDSA",
        asset_type=AssetType.ALGORITHM,
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        location="sig.py"
    )
    # Asset 2: Vulnerable (RSA)
    a2 = CryptoAsset(
        scan_id=scan.id,
        name="RSA Key",
        algorithm_name="RSA",
        asset_type=AssetType.ALGORITHM,
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        location="rsa.py"
    )
    # Asset 3: Safe (AES)
    a3 = CryptoAsset(
        scan_id=scan.id,
        name="AES Key",
        algorithm_name="AES-256-GCM",
        asset_type=AssetType.ALGORITHM,
        purpose=CryptoPurpose.ENCRYPTION,
        quantum_safety=QuantumSafety.QUANTUM_SAFE,
        location="cipher.py"
    )
    db_session.add_all([a1, a2, a3])
    db_session.commit()

    # Call risk summary when 0 RiskAssessment records exist
    service = RiskService(db_session)
    summary = service.get_project_risk_summary(project.id)

    assert summary["total_assets"] == 3
    assert summary["assessed_assets"] == 0
    assert summary["unassessed_assets"] == 3
    assert summary["quantum_vulnerable_count"] == 2
    assert summary["quantum_resistant_count"] == 1
    # Risk counts and averages MUST be based only on persisted RiskAssessment records!
    assert summary["risk_counts"] == {"low": 0, "moderate": 0, "high": 0, "critical": 0}
    assert summary["high_or_critical_risk_assets"] == 0
    assert summary["average_risk_score"] == 0.0

def test_persisted_risk_assessment_updates_risk_counts(db_session):
    project = Project(name="Persisted Assessment Project")
    db_session.add(project)
    db_session.commit()

    scan = Scan(project_id=project.id, target_path="/app", scan_type="AST", status="COMPLETED")

    db_session.add(scan)
    db_session.commit()

    a1 = CryptoAsset(
        scan_id=scan.id,
        name="RSA Key",
        algorithm_name="RSA-2048",
        asset_type=AssetType.ALGORITHM,
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        location="rsa.py"
    )
    db_session.add(a1)
    db_session.commit()

    # Store a real persisted RiskAssessment
    risk_repo = RiskRepository(db_session)
    risk_repo.store_assessment(a1.id, {
        "risk_score": 85.0,
        "risk_level": RiskLevel.CRITICAL,
        "quantum_exposure": 90.0,
        "quantum_status": "QUANTUM_VULNERABLE",
        "crypto_purpose": "DIGITAL_SIGNATURE",
        "priority": "P0"
    })

    service = RiskService(db_session)
    summary = service.get_project_risk_summary(project.id)

    assert summary["total_assets"] == 1
    assert summary["assessed_assets"] == 1
    assert summary["unassessed_assets"] == 0
    assert summary["risk_counts"]["critical"] == 1
    assert summary["high_or_critical_risk_assets"] == 1
    assert summary["average_risk_score"] == 85.0
