from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TechnicalAssessmentSchema(BaseModel):
    quantum_safety: str
    risk_level: str
    risk_score: float
    mosca_status: str
    quantum_threat_horizon: int = 2033

class BusinessContextSchema(BaseModel):
    system_criticality: str
    effective_planning_criticality: str
    user_focus: bool = False
    is_user_adjusted: bool = False
    adjustment_reason: Optional[str] = None

class PrioritizedAssetSchema(BaseModel):
    asset_id: str
    asset_name: str
    algorithm_name: str
    location: str
    line_number: Optional[int] = None
    priority_tier: str  # P1, P2, P3
    priority_rank: int
    technical_assessment: TechnicalAssessmentSchema
    business_context: BusinessContextSchema
    reasons: List[str]

class UserContextUpdateRequest(BaseModel):
    asset_id: str
    user_focus: Optional[bool] = None
    effective_planning_criticality: Optional[str] = None
    adjustment_reason: Optional[str] = None

class PrioritizationSummaryResponse(BaseModel):
    project_id: str
    total_assets: int
    p1_count: int
    p2_count: int
    p3_count: int
    user_focused_count: int
    user_adjusted_count: int
    prioritized_queue: List[PrioritizedAssetSchema]
