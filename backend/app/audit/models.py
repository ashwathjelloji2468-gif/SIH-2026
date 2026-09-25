from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuditArtifactType(str, Enum):
    CBOM_SNAPSHOT = "cbom_snapshot"
    RISK_ASSESSMENT_SNAPSHOT = "risk_assessment_snapshot"
    RECOMMENDATION_SNAPSHOT = "recommendation_snapshot"
    MIGRATION_VALIDATION_RESULT = "migration_validation_result"


class AuditStatus(str, Enum):
    READY = "READY"
    UNCONFIGURED = "UNCONFIGURED"
    ERROR = "ERROR"


class AuditResult(BaseModel):
    status: AuditStatus
    artifact_type: str
    artifact_id: str
    digest: str
    transaction_id: Optional[str] = None
    network: Optional[str] = None
    provider_name: str
    timestamp: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    model_config = {
        "use_enum_values": True,
    }
