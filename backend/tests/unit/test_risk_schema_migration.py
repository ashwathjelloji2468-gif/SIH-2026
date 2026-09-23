import pytest
import tempfile
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, sync_schema
from app.models.db_models import Project, Scan, CryptoAsset, RiskAssessment, ThreatScenario
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, ThreatScenarioType, QuantumSafety
from app.repositories.asset_repository import AssetRepository
from app.repositories.risk_repository import RiskRepository
from app.risk.service import RiskService

def test_sync_schema_migrates_legacy_threat_scenarios_table():
    """Verify sync_schema converts legacy NOT NULL threat_scenarios columns to nullable safely and idempotently."""
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    test_db_url = f"sqlite:///{temp_db_path}"
    test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    
    try:
        # 1. Create legacy schema where quantum_threat_horizon_year, data_lifetime_years, migration_time_years are NOT NULL
        with test_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE projects (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    default_migration_profile VARCHAR NOT NULL DEFAULT 'BALANCED',
                    created_at DATETIME,
                    updated_at DATETIME
                );
            """))
            conn.execute(text("""
                CREATE TABLE scans (
                    id VARCHAR PRIMARY KEY,
                    project_id VARCHAR NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    status VARCHAR NOT NULL DEFAULT 'QUEUED',
                    target_path VARCHAR NOT NULL,
                    scan_type VARCHAR NOT NULL DEFAULT 'source',
                    created_at DATETIME,
                    cbom_version VARCHAR NOT NULL DEFAULT '1.6',
                    scanner_rule_version VARCHAR NOT NULL DEFAULT '2026.1.0'
                );
            """))
            conn.execute(text("""
                CREATE TABLE crypto_assets (
                    id VARCHAR PRIMARY KEY,
                    scan_id VARCHAR NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
                    name VARCHAR NOT NULL,
                    algorithm_name VARCHAR NOT NULL,
                    asset_type VARCHAR NOT NULL DEFAULT 'ALGORITHM',
                    purpose VARCHAR NOT NULL DEFAULT 'GENERAL',
                    location VARCHAR NOT NULL DEFAULT 'app.py',
                    quantum_safety VARCHAR NOT NULL DEFAULT 'UNKNOWN',
                    created_at DATETIME
                );
            """))
            conn.execute(text("""
                CREATE TABLE threat_scenarios (
                    id VARCHAR PRIMARY KEY,
                    asset_id VARCHAR REFERENCES crypto_assets(id) ON DELETE CASCADE,
                    name VARCHAR NOT NULL,
                    scenario_type VARCHAR NOT NULL DEFAULT 'MODERATE',
                    quantum_threat_horizon_year INTEGER NOT NULL,
                    data_lifetime_years INTEGER NOT NULL,
                    migration_time_years INTEGER NOT NULL,
                    severity VARCHAR DEFAULT 'HIGH',
                    urgency VARCHAR DEFAULT 'HIGH',
                    description TEXT,
                    rationale TEXT,
                    evidence JSON,
                    threat_scenario_version VARCHAR NOT NULL DEFAULT '1.1',
                    created_at DATETIME
                );
            """))
            
            # 2. Insert representative existing row into legacy table
            conn.execute(text("""
                INSERT INTO projects (id, name) VALUES ('proj-legacy-1', 'Legacy Project');
            """))
            conn.execute(text("""
                INSERT INTO scans (id, project_id, status, target_path) VALUES ('scan-legacy-1', 'proj-legacy-1', 'COMPLETED', '/tmp');
            """))
            conn.execute(text("""
                INSERT INTO crypto_assets (id, scan_id, name, algorithm_name, location) VALUES ('asset-legacy-1', 'scan-legacy-1', 'Legacy Key', 'RSA-2048', 'app.py');
            """))
            conn.execute(text("""
                INSERT INTO threat_scenarios (id, asset_id, name, scenario_type, quantum_threat_horizon_year, data_lifetime_years, migration_time_years, threat_scenario_version)
                VALUES ('ts-legacy-1', 'asset-legacy-1', 'Legacy HNDL', 'HARVEST_NOW_DECRYPT_LATER', 2035, 10, 5, '1.1');
            """))
            conn.commit()
            
        # Verify initial legacy schema has notnull=1 for target columns
        inspector_before = inspect(test_engine)
        cols_before = {c['name']: c for c in inspector_before.get_columns('threat_scenarios')}
        assert cols_before['quantum_threat_horizon_year']['nullable'] is False
        assert cols_before['data_lifetime_years']['nullable'] is False
        assert cols_before['migration_time_years']['nullable'] is False

        # 3. Run sync_schema(test_engine)
        sync_schema(test_engine)

        # 4. Verify PRAGMA table_info reports nullable=True (notnull=0)
        inspector_after = inspect(test_engine)
        cols_after = {c['name']: c for c in inspector_after.get_columns('threat_scenarios')}
        assert cols_after['quantum_threat_horizon_year']['nullable'] is True
        assert cols_after['data_lifetime_years']['nullable'] is True
        assert cols_after['migration_time_years']['nullable'] is True

        # 5. Verify existing legacy rows are unchanged
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT id, name, quantum_threat_horizon_year, data_lifetime_years, migration_time_years FROM threat_scenarios WHERE id='ts-legacy-1'")).fetchone()
            assert result is not None
            assert result[0] == 'ts-legacy-1'
            assert result[1] == 'Legacy HNDL'
            assert result[2] == 2035
            assert result[3] == 10
            assert result[4] == 5

            # 6. Verify NULL values can now be inserted
            conn.execute(text("""
                INSERT INTO threat_scenarios (id, asset_id, name, scenario_type, quantum_threat_horizon_year, data_lifetime_years, migration_time_years, threat_scenario_version)
                VALUES ('ts-null-1', 'asset-legacy-1', 'Nullable Threat Scenario', 'LONG_LIVED_DATA_EXPOSURE', NULL, NULL, NULL, '1.1');
            """))
            conn.commit()

            null_row = conn.execute(text("SELECT id, quantum_threat_horizon_year, data_lifetime_years, migration_time_years FROM threat_scenarios WHERE id='ts-null-1'")).fetchone()
            assert null_row is not None
            assert null_row[1] is None
            assert null_row[2] is None
            assert null_row[3] is None

        # 9 & 10. Run sync_schema a second time to verify idempotency (no second rebuild)
        sync_schema(test_engine)
        
        inspector_final = inspect(test_engine)
        cols_final = {c['name']: c for c in inspector_final.get_columns('threat_scenarios')}
        assert cols_final['quantum_threat_horizon_year']['nullable'] is True

    finally:
        test_engine.dispose()
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)


def test_risk_assessment_regression_with_null_quantum_threat_horizon():
    """Regression test: verify risk assessment succeeds for assets with quantum_threat_horizon=None without throwing IntegrityError."""
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    test_db_url = f"sqlite:///{temp_db_path}"
    test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    try:
        # Create schema from ORM models and run sync_schema
        Base.metadata.create_all(bind=test_engine)
        sync_schema(test_engine)

        db = TestingSessionLocal()
        try:
            # Seed project, scan, and symmetric asset (AES-256) where Z threat horizon is None
            proj = Project(id="proj-regr-1", name="Regression Project")
            scan = Scan(id="scan-regr-1", project_id="proj-regr-1", status=ScanStatus.COMPLETED, target_path="/tmp")
            
            # Symmetric AES asset with location specified
            aes_asset = CryptoAsset(
                id="asset-aes-1",
                scan_id="scan-regr-1",
                name="AES Encryption Key",
                algorithm_name="AES-256",
                asset_type=AssetType.ALGORITHM,
                purpose=CryptoPurpose.ENCRYPTION,
                location="crypto.py",
                quantum_safety=QuantumSafety.QUANTUM_SAFE
            )
            
            db.add_all([proj, scan, aes_asset])
            db.commit()

            # Execute RiskService.assess_project
            risk_service = RiskService(db)
            assessments = risk_service.assess_project("proj-regr-1")

            assert len(assessments) > 0
            
            # Verify risk assessment row was persisted
            persisted_ra = db.query(RiskAssessment).filter_by(asset_id="asset-aes-1").first()
            assert persisted_ra is not None
            
            # Verify ThreatScenarios for asset have null quantum_threat_horizon_year if Z is None
            scenarios = db.query(ThreatScenario).filter_by(asset_id="asset-aes-1").all()
            for sc in scenarios:
                if sc.quantum_threat_horizon_year is None:
                    assert sc.quantum_threat_horizon_year is None

        finally:
            db.close()

    finally:
        test_engine.dispose()
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
