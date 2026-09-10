"""
Unified Configuration for the Mosca Risk Engine (X + Y - Z).

Centralizes all default assumptions, threat horizons, baseline tables,
and scenario mappings for SENTRIQ.
"""

MOSCA_CONFIG = {
    "default_x_years": 20,
    "default_y_scenario": "STANDARD",
    "default_y_years": 10,
    "default_quantum_horizon": 10,  # T_Q = 10 years (relative horizon: ~2036)
    "current_year": 2026,
    "migration_scenarios": {
        "FAST": 5,
        "STANDARD": 10,
        "COMPLEX": 15,
        "LEGACY_HEAVY": 20
    }
}

# Centralized Z Score to Planning Horizon (years) Mapping Table
# Higher Z_score (higher relative quantum exposure/urgency) -> Shorter Z_planning_horizon_years
Z_SCORE_LOOKUP_TABLE = [
    {"min_score": 20.0, "max_score": float("inf"), "horizon_years": 3, "description": "Critical Quantum Exposure (3-year migration horizon)"},
    {"min_score": 15.0, "max_score": 20.0, "horizon_years": 5, "description": "Extreme Quantum Exposure (5-year migration horizon)"},
    {"min_score": 10.0, "max_score": 15.0, "horizon_years": 7, "description": "High Quantum Exposure (7-year migration horizon)"},
    {"min_score": 6.0, "max_score": 10.0, "horizon_years": 10, "description": "Elevated Quantum Exposure (10-year threat horizon)"},
    {"min_score": 3.0, "max_score": 6.0, "horizon_years": 15, "description": "Moderate Quantum Exposure (15-year threat horizon)"},
    {"min_score": 0.0, "max_score": 3.0, "horizon_years": 20, "description": "Low Quantum Exposure (20-year threat horizon)"},
]

def map_z_score_to_horizon(z_score: float) -> tuple:
    """Maps a relative Z_score to (z_planning_horizon_years, z_target_year)."""
    current_year = MOSCA_CONFIG.get("current_year", 2026)
    for entry in Z_SCORE_LOOKUP_TABLE:
        if entry["min_score"] <= z_score < entry["max_score"]:
            horizon = entry["horizon_years"]
            return horizon, current_year + horizon
    return 20, current_year + 20

