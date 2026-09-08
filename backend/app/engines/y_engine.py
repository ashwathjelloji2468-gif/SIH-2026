from typing import Dict, Any, Optional
from app.config.migration_scenarios import (
    MIGRATION_SCENARIOS, DEFAULT_Y_SCENARIO, DEFAULT_Y_YEARS, get_scenario_info
)

class YEngine:
    """
    Dedicated Y Engine — Migration Time Engine for SENTRIQ.
    Determines Y: estimated time required for cryptographic migration (planning assumption).
    
    Y = Y_scenario (FAST: 5y, STANDARD: 10y, COMPLEX: 15y, LEGACY_HEAVY: 20y).
    Default MVP scenario: STANDARD (10 years).
    """

    def evaluate_y(self, user_scenario: Optional[str] = None) -> Dict[str, Any]:
        has_user_input = bool(user_scenario and user_scenario.upper() in MIGRATION_SCENARIOS)
        scenario_key = user_scenario.upper() if has_user_input else DEFAULT_Y_SCENARIO
        info = get_scenario_info(scenario_key)

        if has_user_input:
            explanation = (
                f"User-selected migration planning scenario '{info['title']}' active ({info['value']} years horizon). "
                f"{info['description']}"
            )
            source = "USER_SELECTED"
        else:
            explanation = (
                "Migration duration cannot be precisely inferred from source code alone. "
                "The MVP therefore uses a standardized 10-year migration planning assumption unless another scenario is selected."
            )
            source = "SYSTEM_DEFAULT"

        return {
            "value": info["value"],
            "unit": "years",
            "scenario": info["key"],
            "scenarioTitle": info["title"],
            "source": source,
            "explanation": explanation,
            "details": info["details"]
        }
