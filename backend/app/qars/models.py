from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from app.qars.config import QARSLevel


class QARSValidationError(ValueError):
    """Raised when QARS inputs fail validation criteria."""
    pass


class QARSCoreInput(BaseModel):
    """
    Inputs required for QARS Core evaluation.
    - x_years (X): Data shelf-life (> 0)
    - y_years (Y): Migration duration (>= 0)
    - z_years (Z): Quantum vulnerability horizon (> 0)
    - data_sensitivity (S): Business data sensitivity (1.0 to 5.0)
    - exposure (E): System exposure / criticality (1.0 to 5.0)
    """
    x_years: float = Field(..., description="Data shelf-life in years (X > 0)")
    y_years: float = Field(..., description="Migration duration in years (Y >= 0)")
    z_years: float = Field(..., description="Quantum vulnerability horizon in years (Z > 0)")
    data_sensitivity: float = Field(..., description="Sensitivity rating S (1..5)")
    exposure: float = Field(..., description="Exposure rating E (1..5)")


class QARSCoreOutput(BaseModel):
    """
    Output produced by QARS Core calculation.
    """
    score: float = Field(..., description="QARS Core score (0..100)")
    timeline_pressure: float = Field(..., description="Normalized timeline pressure T (0..1)")
    sensitivity_normalized: float = Field(..., description="Normalized sensitivity Sn (0..1)")
    exposure_normalized: float = Field(..., description="Normalized exposure En (0..1)")
    x_years: float
    y_years: float
    z_years: float


class QARSAlgorithmRisk(BaseModel):
    """
    Phase 2 Algorithm-Specific Quantum Risk (AQR) evaluation result.
    """
    algorithm: str
    canonical_algorithm: str
    attack_family: str
    vulnerability_factor: Optional[float] = None
    security_strength_factor: Optional[float] = None
    aqr_score: Optional[float] = None
    calibration_status: str
    confidence: str
    quantum_attack: str
    explanation: str
    security_objectives: List[str] = Field(default_factory=list)
    calibration_version: Optional[str] = "SENTRIQ QARS Prototype Heuristic Calibration v1"
    calibration_source: Optional[str] = "SENTRIQ_PROTOTYPE_HEURISTIC"
    calibration_methodology: Optional[str] = None
    calibration_confidence: Optional[str] = None


class SecurityObjectiveResult(BaseModel):
    """
    Phase 2 Security Objective resolution result.
    """
    objectives: List[str]
    purpose_used: str
    source: str


class QARSAvailability(BaseModel):
    """
    Phase 3A Availability scoring result.
    score: normalized AV_base in [0, 1]
    availability_score: AV_base * 100 in [0, 100]
    raw_rating: raw availabilityImpact rating in [1, 5]
    provenance: USER_OVERRIDE | APPLICATION_DEFAULT
    status: CONFIGURED | UNCONFIGURED
    missing_factors: list of unavailable availability metrics
    evidence: secondary unweighted evidence (blast radius score, affected nodes)
    explanation: human-readable calculation explanation
    """
    score: float
    raw_rating: float
    provenance: str
    status: str
    missing_factors: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    explanation: str
    availability_score: Optional[float] = None


class QARSCryptoAgilityEvidence(BaseModel):
    """
    Phase 4 Crypto-Agility Evidence structure.
    agility_score: normalized readiness score [0, 100] (or None if UNCONFIGURED)
    car_score: 100 - agility_score (CAR risk contribution)
    status: CONFIGURED | PARTIALLY_CONFIGURED | UNCONFIGURED
    factors: dictionary of observable evidence values
    provenance: mapping of evidence factor keys to provenance labels
    missing_factors: list of unavailable crypto-agility factors
    """
    status: str
    factors: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, str] = Field(default_factory=dict)
    missing_factors: List[str] = Field(default_factory=list)

    # Phase 3B Structural Factors
    hard_coded_algorithm_ratio: Optional[float] = None
    hard_coded_algorithm_ratio_status: str = "UNCONFIGURED"
    hard_coded_algorithm_ratio_confidence: Optional[float] = None

    crypto_abstraction_layer_presence: Optional[bool] = None
    crypto_abstraction_layer_status: str = "UNCONFIGURED"
    crypto_abstraction_layer_confidence: Optional[float] = None

    replaceable_library_interface_count: Optional[int] = None
    replaceable_library_interface_status: str = "UNCONFIGURED"
    replaceable_library_interface_confidence: Optional[float] = None

    evidence_files: List[str] = Field(default_factory=list)

    # Phase 4 Agility & CAR Scores
    agility_score: Optional[float] = None
    car_score: Optional[float] = None
    calibration_version: str = "SENTRIQ QARS Prototype Heuristic Agility Calibration v1"


class QARSPolicyInput(BaseModel):
    """
    Policy input model, supporting component extensions.
    """
    core_input: Optional[QARSCoreInput] = None
    algorithm_risk: Optional[Union[QARSAlgorithmRisk, float]] = None
    availability: Optional[Union[QARSAvailability, float]] = None
    crypto_agility: Optional[Union[QARSCryptoAgilityEvidence, float]] = None
    migration_complexity: Optional[Union[Any, float]] = None
    security_objectives: Optional[Union[SecurityObjectiveResult, Dict[str, Any], List[str]]] = None
    z_uncertainty: Optional[Any] = None


class QARSExplanation(BaseModel):
    """
    Structured explanatory data for QARS evaluation.
    Contains all exact inputs, intermediate calculations, active adjustments,
    and final score/level outputs.
    """
    x_years: float
    y_years: float
    z_years: float
    data_sensitivity: float
    exposure: float
    sensitivity_normalized: float
    exposure_normalized: float
    timeline_pressure: float
    core_score: float
    active_adjustments: Dict[str, float]
    final_score: float
    severity_level: str
    algorithm_risk: Optional[QARSAlgorithmRisk] = None
    security_objectives: Optional[List[str]] = None
    availability: Optional[QARSAvailability] = None
    crypto_agility_evidence: Optional[QARSCryptoAgilityEvidence] = None
    migration_complexity: Optional[Any] = None
    z_uncertainty: Optional[Any] = None


class QARSResult(BaseModel):
    """
    Final result returned by QARS Policy Engine.
    """
    base_score: float
    adjustments: Dict[str, float]
    final_score: float
    level: QARSLevel
    explanation: QARSExplanation
    algorithm_risk: Optional[QARSAlgorithmRisk] = None
    availability: Optional[QARSAvailability] = None
    crypto_agility_evidence: Optional[QARSCryptoAgilityEvidence] = None
    migration_complexity: Optional[Any] = None
    z_uncertainty: Optional[Any] = None


class QARSProvenance(BaseModel):
    """
    Source metadata for resolved QARS runtime inputs.
    """
    x_source: str
    y_source: str
    z_source: str
    s_source: str
    e_source: str


class QARSRuntimeResult(BaseModel):
    """
    Artifact-level QARS evaluation result with full runtime provenance and metadata.
    """
    asset_id: str
    project_id: Optional[str] = None
    scan_id: Optional[str] = None
    provenance: QARSProvenance
    core_input: QARSCoreInput
    base_score: float
    adjustments: Dict[str, float]
    final_score: float
    level: QARSLevel
    explanation: QARSExplanation
    algorithm_risk: Optional[QARSAlgorithmRisk] = None
    availability: Optional[QARSAvailability] = None
    crypto_agility_evidence: Optional[QARSCryptoAgilityEvidence] = None
    migration_complexity: Optional[Any] = None
    z_uncertainty: Optional[Any] = None

