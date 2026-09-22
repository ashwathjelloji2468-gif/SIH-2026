from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.qars.config import QARSLevel


class QARSAssetSummarySchema(BaseModel):
    """
    API Response schema for asset-level QARS evaluation.
    Ready for GET /assets/{asset_id}/qars
    """
    asset_id: str
    project_id: Optional[str] = None
    scan_id: Optional[str] = None
    qars_score: Optional[float] = Field(None, description="Final bounded QARS score [0, 100]")
    base_score: Optional[float] = Field(None, description="QARS Core base score [0, 100]")
    severity_level: QARSLevel
    timeline_pressure: Optional[float] = None
    x_years: float
    y_years: float
    z_years: Optional[float] = None
    data_sensitivity: float
    exposure: float
    adjustments: Dict[str, float] = Field(default_factory=dict)
    provenance: Dict[str, str] = Field(default_factory=dict)
    algorithm_risk: Optional[Dict[str, Any]] = None
    availability: Optional[Dict[str, Any]] = None
    crypto_agility: Optional[Dict[str, Any]] = None
    migration_complexity: Optional[Dict[str, Any]] = None
    z_uncertainty: Optional[Dict[str, Any]] = None


class QARSProjectSummarySchema(BaseModel):
    """
    API Response schema for project-level QARS aggregate evaluation.
    Ready for GET /projects/{project_id}/qars
    """
    project_id: str
    project_name: str = "Project"
    asset_count: int
    summary: Dict[str, Any]
    assets: List[Any] = Field(default_factory=list)


class QARSResponseSchema(BaseModel):
    """
    Generic QARS response wrapper schema.
    """
    status: str = "SUCCESS"
    data: Any
    message: str = "QARS evaluation completed successfully."
