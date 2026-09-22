from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class QARSZUncertainty(BaseModel):
    """
    Phase 4 Z Uncertainty Result model.
    Preserves categorical ZEngine confidence without fabricating timeline bounds.
    """
    z_low: Optional[float] = None
    z_central: Optional[float] = Field(None, description="Central Z deadline years from ZEngine")
    z_high: Optional[float] = None
    confidence: str = Field(..., description="Categorical ZEngine confidence: HIGH, MEDIUM, LOW")
    status: str = "POINT_ESTIMATE_ONLY"
    source: str = "Z_ENGINE"
    explanation: str = "QARS currently uses the deterministic ZEngine central planning horizon. Statistical lower/upper timeline bounds are not currently available."


def evaluate_z_uncertainty(z_result: Dict[str, Any]) -> QARSZUncertainty:
    """
    Evaluates Z uncertainty for QARS Phase 4.
    Preserves central Z_i value and categorical confidence from ZEngine without inventing statistical bounds.
    """
    z_val = z_result.get("z_value")
    if z_val is None:
        z_val = z_result.get("value_years_remaining")
    if z_val is None:
        z_val = z_result.get("z_planning_horizon_years")

    z_central = float(z_val) if z_val is not None and isinstance(z_val, (int, float)) and z_val > 0 else None
    conf = str(z_result.get("confidence", "HIGH")).upper()
    if conf not in ["HIGH", "MEDIUM", "LOW"]:
        conf = "HIGH"

    return QARSZUncertainty(
        z_low=None,
        z_central=z_central,
        z_high=None,
        confidence=conf,
        status="POINT_ESTIMATE_ONLY",
        source="Z_ENGINE",
        explanation="QARS currently uses the deterministic ZEngine central planning horizon. Statistical lower/upper timeline bounds are not currently available."
    )
