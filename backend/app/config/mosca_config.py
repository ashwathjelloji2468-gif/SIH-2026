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
