from typing import Dict, Any

def estimate_migration_effort(
    affected_assets_count: int,
    dependency_count: int = 2,
    has_custom_crypto: bool = False,
    crypto_agility_score: float = 0.5, # 0.0 (rigid) to 1.0 (agile)
    team_capacity_developers: int = 3
) -> Dict[str, Any]:
    """
    Estimates migration effort from observable project variables:
    - Output 1: PERSON-EFFORT (person-days / person-months)
    - Output 2: CALENDAR DURATION (months based on team capacity & dependencies)
    """
    base_days_per_asset = 5.0
    if has_custom_crypto:
        base_days_per_asset *= 2.0

    # Adjust for crypto-agility (more agile = fewer days)
    agility_factor = 1.5 - (crypto_agility_score * 0.8)
    
    total_person_days = round(affected_assets_count * base_days_per_asset * agility_factor * (1 + 0.1 * dependency_count), 1)
    total_person_months = round(total_person_days / 20.0, 1)

    # Calculate calendar duration considering team size and sequential dependencies
    parallel_efficiency = min(1.0, 0.7 + (0.1 * team_capacity_developers))
    working_days_per_month = 20.0
    
    calendar_months = round(total_person_days / (team_capacity_developers * working_days_per_month * parallel_efficiency), 1)
    calendar_months = max(0.5, calendar_months)

    assumptions = {
        "base_days_per_asset": base_days_per_asset,
        "crypto_agility_score": crypto_agility_score,
        "team_capacity_developers": team_capacity_developers,
        "parallel_efficiency": parallel_efficiency
    }

    return {
        "person_days": total_person_days,
        "person_months": total_person_months,
        "calendar_months": calendar_months,
        "assumptions": assumptions
    }
