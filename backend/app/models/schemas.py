from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import (
    ScanStatus, AssetType, CryptoPurpose, RiskLevel, EvidenceType,
    StandardStatus, ThreatScenarioType, ValidationStatus, QuantumSafety, ReviewStatus, TestingRequirement
)

# Health Schema
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.2.0"
    database: str = "connected"
    versions: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime

# Project Schemas
class ProjectBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Enterprise Payments Service"})
    description: Optional[str] = Field(None, json_schema_extra={"example": "Core transaction processing backend"})
    repository_url: Optional[str] = Field(None, json_schema_extra={"example": "https://github.com/org/repo.git"})

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    repository_url: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Scan Schemas
class ScanCreate(BaseModel):
    target_path: str = Field(..., json_schema_extra={"example": "/app/source"})
    scan_type: str = Field("source", json_schema_extra={"example": "source"})

class ScanResponse(BaseModel):
    id: str
    project_id: str
    status: ScanStatus
    target_path: str
    scan_type: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    cbom_version: str
    scanner_rule_version: str = "2026.1.0"

    model_config = ConfigDict(from_attributes=True)

# Evidence Schemas
class EvidenceResponse(BaseModel):
    id: str
    asset_id: str
    evidence_type: EvidenceType
    source_file: str
    line_number: Optional[int] = None
    detector_name: str
    detector_version: str
    excerpt: Optional[str] = None
    confidence_score: float
    provenance: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Crypto Asset Schemas
class CryptoAssetResponse(BaseModel):
    id: str
    scan_id: str
    name: str
    asset_type: AssetType
    algorithm_name: str
    key_size: Optional[int] = None
    purpose: CryptoPurpose
    location: str
    line_number: Optional[int] = None
    quantum_safety: QuantumSafety
    is_unknown: bool = False
    unknown_reason: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.RESOLVED
    created_at: datetime
    evidence_items: List[EvidenceResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ReviewAssetRequest(BaseModel):
    algorithm_name: Optional[str] = None
    purpose: Optional[CryptoPurpose] = None
    action: str = Field("RESOLVE", json_schema_extra={"example": "RESOLVE"})  # RESOLVE or REJECT

# Coverage Schemas
class CategoryCoverage(BaseModel):
    category_name: str
    scanned_count: int
    coverage_percentage: float
    notes: str

class CoverageReportResponse(BaseModel):
    project_id: str
    overall_coverage_percentage: float
    categories: List[CategoryCoverage]
    total_assets_discovered: int
    unknown_needs_review_count: int
    disclaimer: str = "ECDAT explicitly communicates limitations and coverage. 100% cryptographic discovery is never claimed."

# Risk Assessment Schemas
class RiskAssessRequest(BaseModel):
    asset_id: Optional[str] = None
    project_id: Optional[str] = None
    data_sensitivity_label: Optional[str] = "UNKNOWN"
    business_criticality_label: Optional[str] = "UNKNOWN"
    data_lifetime_years: Optional[float] = 10.0
    migration_time_years: Optional[float] = 3.0
    quantum_threat_horizon_year: Optional[int] = 2033
    force_reassessment: Optional[bool] = True

class RiskAssessmentResponse(BaseModel):
    id: str
    asset_id: str
    risk_score: float
    risk_level: RiskLevel
    quantum_vulnerability_score: float
    data_sensitivity_score: float
    business_criticality_score: float
    mosca_factor_score: float
    exposure_score: float
    migration_complexity_score: float
    explanation: Optional[str] = None
    confidence_score: float
    risk_model_version: str = "2.0-MOSCA"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Recommendation Schemas
class RecommendationResponse(BaseModel):
    id: str
    asset_id: str
    target_pqc_candidate: str
    standard_status: StandardStatus
    rationale: str
    compatibility_notes: Optional[str] = None
    performance_notes: Optional[str] = None
    migration_complexity: str
    confidence: float
    kb_version: str = "2026.3.0-NIST-PQC"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Threat Scenario Schemas
class ThreatScenarioBase(BaseModel):
    name: str
    scenario_type: ThreatScenarioType = ThreatScenarioType.MODERATE
    quantum_threat_horizon_year: int = 2033
    data_lifetime_years: int = 10
    migration_time_years: int = 3
    description: Optional[str] = None

class ThreatScenarioCreate(ThreatScenarioBase):
    pass

class ThreatScenarioResponse(ThreatScenarioBase):
    id: str
    threat_scenario_version: str = "1.1"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Migration Plan Schemas
class MigrationPlanCreate(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "PQC Upgrade Phase 1"})
    vendor_dependency_count: Optional[int] = 1
    pki_cert_dependency_count: Optional[int] = 1
    crypto_agility_score: Optional[float] = 0.6
    testing_requirement_level: Optional[TestingRequirement] = TestingRequirement.HIGH
    engineering_capacity_developers: Optional[int] = 3

class MigrationTaskResponse(BaseModel):
    id: str
    plan_id: str
    project_id: Optional[str] = None
    asset_id: str
    recommendation_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = "ALGORITHM_REPLACEMENT"
    priority: Optional[str] = "P2"
    migration_complexity: Optional[str] = "MEDIUM"
    person_days: float = 1.0
    sequence_order: int = 1
    status: str = "NOT_STARTED"
    affected_components: List[str] = []
    dependencies: List[str] = []
    blockers: List[str] = []
    validation_requirements: List[str] = []
    rationale: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class MigrationPlanResponse(BaseModel):
    id: str
    project_id: str
    name: str
    total_person_days: float
    total_calendar_months: float
    assumptions: Optional[Dict[str, Any]] = None
    created_at: datetime
    tasks: List[MigrationTaskResponse] = []

    model_config = ConfigDict(from_attributes=True)

# Validation & Simulation Schemas
class MigrationSimulationResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    asset_id: str
    recommendation_id: Optional[str] = None
    migration_plan_id: Optional[str] = None
    status: str
    sandbox_path: Optional[str] = None
    transformation_type: Optional[str] = None
    files_changed: List[str] = []
    changes_summary: Optional[Dict[str, Any]] = None
    before_fingerprint: Optional[str] = None
    after_fingerprint: Optional[str] = None
    build_result: Optional[Dict[str, Any]] = None
    test_result: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    failure_reason: Optional[str] = None
    blocker_reason: Optional[str] = None
    confidence: float = 1.0
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ValidationRunResponse(BaseModel):
    id: str
    simulation_id: Optional[str] = None
    plan_id: Optional[str] = None
    asset_id: Optional[str] = None
    check_type: str = "BUILD"
    status: str = "PENDING"
    command: Optional[str] = None
    exit_code: Optional[int] = None
    output_summary: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    duration: float = 0.0
    build_passed: bool = False
    unit_tests_passed: bool = False
    crypto_tests_passed: bool = False
    integration_tests_passed: bool = False
    regression_passed: bool = False
    api_compatible: bool = False
    logs: Optional[str] = None
    residual_risk_score: float = 0.0
    confidence: float = 1.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Audit Schemas
class AuditEventResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    action: str
    actor: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# CBOM Schema (Updated to CycloneDX 1.6 per user request)
class CBOMResponse(BaseModel):
    bomFormat: str = "CycloneDX"
    specVersion: str = "1.6"
    version: int = 1
    metadata: Dict[str, Any]
    components: List[Dict[str, Any]] = []
