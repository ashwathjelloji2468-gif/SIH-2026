import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import (
    ScanStatus, AssetType, CryptoPurpose, RiskLevel, EvidenceType,
    StandardStatus, ThreatScenarioType, ValidationStatus, QuantumSafety, ReviewStatus,
    RecommendationCategory, SimulationStatus, ValidationCheckType, ValidationCheckStatus
)

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    repository_url = Column(String, nullable=True)
    user_x_years = Column(Integer, nullable=True)
    user_domain = Column(String, nullable=True)
    user_y_scenario = Column(String, nullable=True)
    folder_contexts = Column(JSON, nullable=True)
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
    cbom_version = Column(String, default="1.6", nullable=False)
    scanner_rule_version = Column(String, default="2026.1.0", nullable=False)

    # Relationships
    project = relationship("Project", back_populates="scans")
    assets = relationship("CryptoAsset", back_populates="scan", cascade="all, delete-orphan")
    nodes = relationship("CryptoNode", back_populates="scan", cascade="all, delete-orphan")
    edges = relationship("CryptoEdge", back_populates="scan", cascade="all, delete-orphan")
    blast_radius_results = relationship("BlastRadiusResult", back_populates="scan", cascade="all, delete-orphan")

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

    # Unknown / Needs Review Fields
    is_unknown = Column(Boolean, default=False, nullable=False)
    unknown_reason = Column(Text, nullable=True)
    review_status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.RESOLVED, nullable=False)
    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    # Relationships
    scan = relationship("Scan", back_populates="assets")
    evidence_items = relationship("Evidence", back_populates="asset", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="asset", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="asset", cascade="all, delete-orphan")
    threat_scenarios = relationship("ThreatScenario", back_populates="asset", cascade="all, delete-orphan")

    @property
    def classification(self):
        from app.normalization.crypto_asset_normalizer import classify_crypto_asset
        return classify_crypto_asset(
            algorithm_name=self.algorithm_name,
            key_size=self.key_size,
            asset_type=self.asset_type,
            purpose=self.purpose
        )

    @property
    def data_lifetime_years(self) -> float:
        return self.classification["data_lifetime_years"]

    @property
    def lifetime_label(self) -> str:
        return self.classification["lifetime_label"]

    @property
    def business_criticality_label(self) -> str:
        return self.classification["business_criticality_label"]

    @property
    def business_criticality_score(self) -> float:
        return self.classification["business_criticality_score"]

    @property
    def classification_summary(self) -> str:
        return self.classification["classification_summary"]

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
    confidence_score = Column(Float, default=1.0, nullable=False)
    algorithm_name = Column(String, nullable=False)
    purpose = Column(SQLEnum(CryptoPurpose), nullable=False)
    asset_type = Column(SQLEnum(AssetType), nullable=False)
    matched_text = Column(Text, nullable=True)
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
    quantum_exposure = Column(Float, default=0.0)
    quantum_vulnerability_score = Column(Float, default=0.0)
    data_sensitivity_score = Column(Float, default=0.0)
    business_criticality_score = Column(Float, default=0.0)
    mosca_factor_score = Column(Float, default=0.0)
    exposure_score = Column(Float, default=0.0)
    migration_complexity_score = Column(Float, default=0.0)
    lifetime_exposure_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=1.0)
    quantum_status = Column(String, nullable=True)
    crypto_purpose = Column(String, nullable=True)
    mosca_status = Column(String, nullable=True)
    quantum_threat_horizon = Column(Integer, default=2033)
    priority = Column(String, nullable=True)
    explanation = Column(Text, nullable=True)
    rationale = Column(JSON, nullable=True)
    factors = Column(JSON, nullable=True)
    risk_model_version = Column(String, default="2.0-MOSCA", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    asset = relationship("CryptoAsset", back_populates="risk_assessments")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=generate_uuid)
    asset_id = Column(String, ForeignKey("crypto_assets.id", ondelete="CASCADE"), nullable=False)
    risk_assessment_id = Column(String, ForeignKey("risk_assessments.id", ondelete="SET NULL"), nullable=True)
    target_pqc_candidate = Column(String, nullable=False)
    recommended_algorithm = Column(String, nullable=True)
    alternative_algorithm = Column(String, nullable=True)
    category = Column(SQLEnum(RecommendationCategory), default=RecommendationCategory.MANUAL_REVIEW, nullable=False)
    priority = Column(String, default="LOW")
    standard_status = Column(SQLEnum(StandardStatus), default=StandardStatus.FINAL_STANDARD, nullable=False)
    rationale = Column(Text, nullable=False)
    compatibility_notes = Column(Text, nullable=True)
    performance_notes = Column(Text, nullable=True)
    tradeoffs = Column(JSON, nullable=True)
    threat_scenarios = Column(JSON, nullable=True)
    migration_notes = Column(Text, nullable=True)
    migration_complexity = Column(String, default="MEDIUM")
    confidence = Column(Float, default=1.0)
    kb_version = Column(String, default="2026.3.0-NIST-PQC", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    asset = relationship("CryptoAsset", back_populates="recommendations")

    @property
    def latency_impact(self) -> Optional[str]:
        if self.tradeoffs and isinstance(self.tradeoffs, dict):
            return self.tradeoffs.get("latency_impact")
        return None

    @property
    def cost_impact(self) -> Optional[str]:
        if self.tradeoffs and isinstance(self.tradeoffs, dict):
            return self.tradeoffs.get("cost_impact")
        return None

    @property
    def latency_level(self) -> Optional[str]:
        if self.tradeoffs and isinstance(self.tradeoffs, dict):
            return self.tradeoffs.get("latency_level", "LOW")
        return "LOW"

    @property
    def cost_level(self) -> Optional[str]:
        if self.tradeoffs and isinstance(self.tradeoffs, dict):
            return self.tradeoffs.get("cost_level", "MEDIUM")
        return "MEDIUM"

class ThreatScenario(Base):
    __tablename__ = "threat_scenarios"

    id = Column(String, primary_key=True, default=generate_uuid)
    asset_id = Column(String, ForeignKey("crypto_assets.id", ondelete="CASCADE"), nullable=True)
    name = Column(String, nullable=False)
    scenario_type = Column(SQLEnum(ThreatScenarioType), default=ThreatScenarioType.MODERATE, nullable=False)
    quantum_threat_horizon_year = Column(Integer, nullable=False, default=2033)  # Z
    data_lifetime_years = Column(Integer, default=10, nullable=False)  # X
    migration_time_years = Column(Integer, default=3, nullable=False)  # Y
    severity = Column(String, default="HIGH")
    urgency = Column(String, default="HIGH")
    description = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    evidence = Column(JSON, nullable=True)
    threat_scenario_version = Column(String, default="1.1", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    asset = relationship("CryptoAsset", back_populates="threat_scenarios")

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
    project_id = Column(String, nullable=True)
    asset_id = Column(String, nullable=False)
    recommendation_id = Column(String, nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String, default="ALGORITHM_REPLACEMENT")
    priority = Column(String, default="P2")
    migration_complexity = Column(String, default="MEDIUM")
    person_days = Column(Float, default=1.0)
    sequence_order = Column(Integer, default=1)
    status = Column(String, default="NOT_STARTED")
    affected_components = Column(JSON, nullable=True)
    dependencies = Column(JSON, nullable=True)
    blockers = Column(JSON, nullable=True)
    validation_requirements = Column(JSON, nullable=True)
    rationale = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    plan = relationship("MigrationPlan", back_populates="tasks")

class MigrationSimulation(Base):
    __tablename__ = "migration_simulations"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, nullable=True)
    asset_id = Column(String, nullable=False)
    recommendation_id = Column(String, nullable=True)
    migration_plan_id = Column(String, nullable=True)
    status = Column(SQLEnum(SimulationStatus), default=SimulationStatus.CREATED, nullable=False)
    sandbox_path = Column(String, nullable=True)
    transformation_type = Column(String, nullable=True)
    files_changed = Column(JSON, nullable=True)
    changes_summary = Column(JSON, nullable=True)
    before_fingerprint = Column(String, nullable=True)
    after_fingerprint = Column(String, nullable=True)
    build_result = Column(JSON, nullable=True)
    test_result = Column(JSON, nullable=True)
    validation_result = Column(JSON, nullable=True)
    failure_reason = Column(Text, nullable=True)
    blocker_reason = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    validations = relationship("ValidationRun", back_populates="simulation", cascade="all, delete-orphan")

class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    simulation_id = Column(String, ForeignKey("migration_simulations.id", ondelete="CASCADE"), nullable=True)
    plan_id = Column(String, ForeignKey("migration_plans.id", ondelete="CASCADE"), nullable=True)
    asset_id = Column(String, nullable=True)
    check_type = Column(String, default="BUILD")
    status = Column(SQLEnum(ValidationStatus), default=ValidationStatus.PENDING, nullable=False)
    command = Column(String, nullable=True)
    exit_code = Column(Integer, nullable=True)
    output_summary = Column(Text, nullable=True)
    evidence = Column(JSON, nullable=True)
    duration = Column(Float, default=0.0)
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
    simulation = relationship("MigrationSimulation", back_populates="validations")

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

class CryptoNode(Base):
    __tablename__ = "crypto_nodes"

    id = Column(String, primary_key=True, default=generate_uuid)
    scan_id = Column(String, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(String, ForeignKey("crypto_assets.id", ondelete="SET NULL"), nullable=True)
    artefact_type = Column(String, nullable=False, default="ALGORITHM")
    name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=True)
    location = Column(String, nullable=True)
    quantum_risk = Column(String, default="LOW", nullable=False)
    mosca_x = Column(Float, default=10.0, nullable=False)
    business_criticality = Column(Float, default=50.0, nullable=False)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    scan = relationship("Scan", back_populates="nodes")
    asset = relationship("CryptoAsset")
    outgoing_edges = relationship("CryptoEdge", foreign_keys="CryptoEdge.source_node_id", back_populates="source_node", cascade="all, delete-orphan")
    incoming_edges = relationship("CryptoEdge", foreign_keys="CryptoEdge.target_node_id", back_populates="target_node", cascade="all, delete-orphan")
    blast_radius_results = relationship("BlastRadiusResult", back_populates="root_node", cascade="all, delete-orphan")

class CryptoEdge(Base):
    __tablename__ = "crypto_edges"

    id = Column(String, primary_key=True, default=generate_uuid)
    scan_id = Column(String, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    source_node_id = Column(String, ForeignKey("crypto_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_node_id = Column(String, ForeignKey("crypto_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String, nullable=False, default="uses")  # uses, depends_on, shares_key, protects, signs, issued_by
    strength = Column(Float, default=1.0, nullable=False)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    scan = relationship("Scan", back_populates="edges")
    source_node = relationship("CryptoNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("CryptoNode", foreign_keys=[target_node_id], back_populates="incoming_edges")

class BlastRadiusResult(Base):
    __tablename__ = "blast_radius_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    scan_id = Column(String, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    root_node_id = Column(String, ForeignKey("crypto_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    radius_score = Column(Float, nullable=False, default=0.0)
    affected_nodes_count = Column(Integer, default=0, nullable=False)
    systems_count = Column(Integer, default=0, nullable=False)
    data_classes = Column(JSON, nullable=True)
    estimated_migration_effort = Column(Float, default=0.0, nullable=False)
    affected_nodes_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    scan = relationship("Scan", back_populates="blast_radius_results")
    root_node = relationship("CryptoNode", back_populates="blast_radius_results")

