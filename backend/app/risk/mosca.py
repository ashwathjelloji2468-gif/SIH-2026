from datetime import datetime, timezone
from typing import Dict, Any

try:
    from app.core.config import settings
    DEFAULT_HORIZON = getattr(settings, "DEFAULT_QUANTUM_THREAT_HORIZON", 2033)
except Exception:
    DEFAULT_HORIZON = 2033

def calculate_mosca_analysis(
    data_lifetime_years: float = 10.0,       # X
    migration_time_years: float = 3.0,        # Y
    quantum_threat_horizon_year: int = None, # Z
    current_year: int = None
) -> Dict[str, Any]:
    """
    Mosca's Theorem Calculation:
    If X + Y > Z, data security is compromised before migration completes.
    - X: Required data protection lifetime (years)
    - Y: Time required to migrate infrastructure (years)
    - Z: Time until quantum threat (threat horizon)

    Returns:
    - mosca_score (0-100)
    - mosca_status ("SAFE_MARGIN", "MIGRATION_REQUIRED", "DEADLINE_RISK", "UNKNOWN")
    - urgency_gap_years
    - rationale
    - horizon_used
    """
    if quantum_threat_horizon_year is None:
        quantum_threat_horizon_year = DEFAULT_HORIZON

    if current_year is None:
        current_year = datetime.now(timezone.utc).year

    years_until_quantum = max(1.0, float(quantum_threat_horizon_year - current_year))
    protection_window = float(data_lifetime_years + migration_time_years)
    urgency_gap = protection_window - years_until_quantum

    if urgency_gap > 3.0:
        mosca_score = 100.0
        mosca_status = "DEADLINE_RISK"
        rationale = (
            f"DEADLINE RISK: Protection window X+Y ({data_lifetime_years:.1f}y + {migration_time_years:.1f}y = {protection_window:.1f}y) "
            f"exceeds remaining threat horizon Z ({years_until_quantum:.1f}y) by {urgency_gap:.1f} years."
        )
    elif urgency_gap > 0.0:
        mosca_score = 80.0
        mosca_status = "MIGRATION_REQUIRED"
        rationale = (
            f"MIGRATION REQUIRED: Protection window X+Y ({protection_window:.1f}y) exceeds threat horizon Z ({years_until_quantum:.1f}y). "
            f"Migration must begin immediately."
        )
    elif urgency_gap >= -3.0:
        mosca_score = 50.0
        mosca_status = "MIGRATION_REQUIRED"
        rationale = (
            f"MIGRATION REQUIRED: Protection window ({protection_window:.1f}y) approaches threat horizon ({years_until_quantum:.1f}y). "
            f"Margin is narrow ({abs(urgency_gap):.1f}y remaining)."
        )
    else:
        mosca_score = 20.0
        mosca_status = "SAFE_MARGIN"
        rationale = (
            f"SAFE MARGIN: Protection window ({protection_window:.1f}y) completes comfortably within threat horizon Z ({years_until_quantum:.1f}y)."
        )

    return {
        "mosca_score": mosca_score,
        "mosca_status": mosca_status,
        "urgency_gap_years": urgency_gap,
        "quantum_threat_horizon": quantum_threat_horizon_year,
        "years_until_quantum": years_until_quantum,
        "data_lifetime_years": data_lifetime_years,
        "migration_time_years": migration_time_years,
        "protection_window_years": protection_window,
        "rationale": rationale
    }
