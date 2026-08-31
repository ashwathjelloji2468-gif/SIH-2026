import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import (
    ScanStatus, AssetType, CryptoPurpose, RiskLevel, EvidenceType,
    StandardStatus, ThreatScenarioType, ValidationStatus, QuantumSafety
)

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    repository_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    scans = relationship("Scan", back_populates="project", cascade="all, delete-orphan")
    migration_plans = relationship("MigrationPlan", back_populates="project", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="project", cascade="all, delete-orphan")

class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.QUEUED, nullable=False)
    target_path = Column(String, nullable=False)
    scan_type = Column(String, default="source", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    cbom_json = Column(JSON, nullable=True)
    cbom_version = Column(String, default="1.5", nullable=False)

    # Relationships
    project = relationship("Project", back_populates="scans")
    assets = relationship("CryptoAsset", back_populates="scan", cascade="all, delete-orphan")

class CryptoAsset(Base):
    __tablename__ = "crypto_assets"

    id = Column(String, primary_key=True, default=generate_uuid)
    scan_id = Column(String, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False, index=True)
    asset_type = Column(SQLEnum(AssetType), nullable=False)
    algorithm_name = Column(String, nullable=False, index=True)
    key_size = Column(Integer, nullable=True)
    purpose = Column(SQLEnum(CryptoPurpose), default=CryptoPurpose.UNKNOWN, nullable=False)
    location = Column(String, nullable=False)  # File path or reference
    line_number = Column(Integer, nullable=True)
    quantum_safety = Column(SQLEnum(QuantumSafety), default=QuantumSafety.UNKNOWN, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    scan = relationship("Scan", back_populates="assets")
    evidence_items = relationship("Evidence", back_populates="asset", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="asset", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="asset", cascade="all, delete-orphan")

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=generate_uuid)
    asset_id = Column(String, ForeignKey("crypto_assets.id", ondelete="CASCADE"), nullable=False)
    evidence_type = Column(SQLEnum(EvidenceType), default=EvidenceType.OBSERVED, nullable=False)
    source_file = Column(String, nullable=False)
    line_number = Column(Integer, nullable=True)
    detector_name = Column(String, nullable=False)
    detector_version = Column(String, default="1.0.0", nullable=False)
    excerpt = Column(Text, nullable=True)
    confidence_score = Column(Float, default=1.0, nullable=False)  # 0.0 to 1.0
    provenance = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    asset = relationship("CryptoAsset", back_populates="evidence_items")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String, primary_key=True, default=generate_uuid)
    asset_id = Column(String, ForeignKey("crypto_assets.id", ondelete="CASCADE"), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0 to 100
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    quantum_vulnerability_score = Column(Float, default=0.0)
    data_sensitivity_score = Column(Float, default=0.0)
    business_criticality_score = Column(Float, default=0.0)
    mosca_factor_score = Column(Float, default=0.0)
    exposure_score = Column(Float, default=0.0)
    migration_complexity_score = Column(Float, default=0.0)
    explanation = Column(Text, nullable=True)
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    asset = relationship("CryptoAsset", back_populates="risk_assessments")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=generate_uuid)
    asset_id = Column(String, ForeignKey("crypto_assets.id", ondelete="CASCADE"), nullable=False)
    target_pqc_candidate = Column(String, nullable=False)
    standard_status = Column(SQLEnum(StandardStatus), default=StandardStatus.FINAL_STANDARD, nullable=False)
    rationale = Column(Text, nullable=False)
    compatibility_notes = Column(Text, nullable=True)
    performance_notes = Column(Text, nullable=True)
    migration_complexity = Column(String, default="MEDIUM")
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    asset = relationship("CryptoAsset", back_populates="recommendations")

class ThreatScenario(Base):
    __tablename__ = "threat_scenarios"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    scenario_type = Column(SQLEnum(ThreatScenarioType), default=ThreatScenarioType.MODERATE, nullable=False)
    quantum_threat_horizon_year = Column(Integer, nullable=False)  # Z
    data_lifetime_years = Column(Integer, default=10, nullable=False)  # X
    migration_time_years = Column(Integer, default=3, nullable=False)  # Y
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class MigrationPlan(Base):
    __tablename__ = "migration_plans"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    total_person_days = Column(Float, default=0.0)
    total_calendar_months = Column(Float, default=0.0)
    assumptions = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    project = relationship("Project", back_populates="migration_plans")
    tasks = relationship("MigrationTask", back_populates="plan", cascade="all, delete-orphan")
    validations = relationship("ValidationRun", back_populates="plan", cascade="all, delete-orphan")

class MigrationTask(Base):
    __tablename__ = "migration_tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    plan_id = Column(String, ForeignKey("migration_plans.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    person_days = Column(Float, default=1.0)
    sequence_order = Column(Integer, default=1)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    plan = relationship("MigrationPlan", back_populates="tasks")

class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    plan_id = Column(String, ForeignKey("migration_plans.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(ValidationStatus), default=ValidationStatus.PENDING, nullable=False)
    build_passed = Column(Boolean, default=False)
    unit_tests_passed = Column(Boolean, default=False)
    crypto_tests_passed = Column(Boolean, default=False)
    integration_tests_passed = Column(Boolean, default=False)
    regression_passed = Column(Boolean, default=False)
    api_compatible = Column(Boolean, default=False)
    logs = Column(Text, nullable=True)
    residual_risk_score = Column(Float, default=0.0)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    plan = relationship("MigrationPlan", back_populates="validations")

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    action = Column(String, nullable=False, index=True)
    actor = Column(String, default="system")
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    project = relationship("Project", back_populates="audit_events")

# Reference / Knowledge Tables
class Algorithm(Base):
    __tablename__ = "ref_algorithms"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    family = Column(String, nullable=False)
    is_quantum_vulnerable = Column(Boolean, default=True)
    standard_status = Column(SQLEnum(StandardStatus), default=StandardStatus.FINAL_STANDARD)

class AlgorithmPurpose(Base):
    __tablename__ = "ref_algorithm_purposes"

    id = Column(String, primary_key=True, default=generate_uuid)
    algorithm_name = Column(String, nullable=False)
    purpose = Column(SQLEnum(CryptoPurpose), nullable=False)

class Standard(Base):
    __tablename__ = "ref_standards"

    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, nullable=False, unique=True)  # e.g., FIPS 203
    name = Column(String, nullable=False)
    status = Column(SQLEnum(StandardStatus), nullable=False)
    description = Column(Text, nullable=True)

class PQCCandidate(Base):
    __tablename__ = "ref_pqc_candidates"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)  # ML-KEM, ML-DSA, SLH-DSA
    standard_code = Column(String, nullable=False)     # FIPS 203, FIPS 204, FIPS 205
    purpose = Column(SQLEnum(CryptoPurpose), nullable=False)
    status = Column(SQLEnum(StandardStatus), default=StandardStatus.FINAL_STANDARD)
    key_size_notes = Column(Text, nullable=True)

class CompatibilityRule(Base):
    __tablename__ = "ref_compatibility_rules"

    id = Column(String, primary_key=True, default=generate_uuid)
    legacy_algorithm = Column(String, nullable=False)
    pqc_candidate = Column(String, nullable=False)
    compatibility_score = Column(Float, default=1.0)
    notes = Column(Text, nullable=True)

class DataClassification(Base):
    __tablename__ = "ref_data_classifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    level_name = Column(String, nullable=False, unique=True)
    sensitivity_score = Column(Float, nullable=False)  # 0 to 100

class BusinessCriticality(Base):
    __tablename__ = "ref_business_criticalities"

    id = Column(String, primary_key=True, default=generate_uuid)
    level_name = Column(String, nullable=False, unique=True)
    criticality_score = Column(Float, nullable=False)  # 0 to 100
