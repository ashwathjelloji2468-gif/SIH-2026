from typing import Dict, Any
from app.models.enums import TestingRequirement

def estimate_migration_effort(
    affected_assets_count: int,
    affected_apps_count: int = 1,
    dependency_count: int = 2,
    vendor_dependency_count: int = 1,
    pki_cert_dependency_count: int = 1,
    crypto_agility_score: float = 0.5,
    testing_requirement_level: TestingRequirement = TestingRequirement.HIGH,
    business_criticality_score: float = 80.0,
    engineering_capacity_developers: int = 3
) -> Dict[str, Any]:
    """
    Estimates migration effort from observable project variables without hardcoded global algorithm values:
    - PERSON-EFFORT (person-days and person-months)
    - CALENDAR DURATION (months based on team capacity & dependency chains)
    """
    base_days_per_asset = 4.0

    # Agility factor: higher agility reduces effort (0.0 -> 1.5x, 1.0 -> 0.7x)
    agility_factor = max(0.6, 1.5 - (crypto_agility_score * 0.8))

    # Testing overhead multiplier
    testing_multipliers = {
        TestingRequirement.LOW: 1.0,
        TestingRequirement.MEDIUM: 1.2,
        TestingRequirement.HIGH: 1.5,
        TestingRequirement.REGULATED: 1.9
    }
    testing_mult = testing_multipliers.get(testing_requirement_level, 1.5)

    # Dependency multipliers
    vendor_dep_mult = 1.0 + (0.35 * vendor_dependency_count)  # External vendor coordination overhead
    pki_cert_mult = 1.0 + (0.25 * pki_cert_dependency_count)   # CA / PKI infrastructure re-issuance overhead
    criticality_mult = 1.0 + (0.003 * business_criticality_score) # Extra validation for critical systems

    asset_days = affected_assets_count * base_days_per_asset * agility_factor
    app_coordination_days = (affected_apps_count - 1) * 6.0

    total_person_days = (asset_days + app_coordination_days) * testing_mult * vendor_dep_mult * pki_cert_mult * criticality_mult
    total_person_days = round(total_person_days, 1)
    total_person_months = round(total_person_days / 20.0, 1)

    # Calendar duration calculation (considering team size, parallel efficiency, sequential vendor dependencies)
    dev_capacity = max(1, engineering_capacity_developers)
    parallel_efficiency = min(0.9, 0.5 + (0.1 * dev_capacity))
    
    base_calendar_months = total_person_days / (dev_capacity * 20.0 * parallel_efficiency)
    # Add sequential vendor lead time buffer (e.g. 1.5 months per vendor dependency chain)
    vendor_lead_time_months = vendor_dependency_count * 1.5
    
    calendar_months = round(base_calendar_months + vendor_lead_time_months, 1)
    calendar_months = max(0.5, calendar_months)

    assumptions = {
        "affected_assets_count": affected_assets_count,
        "affected_apps_count": affected_apps_count,
        "base_days_per_asset": base_days_per_asset,
        "agility_factor": round(agility_factor, 2),
        "crypto_agility_score": crypto_agility_score,
        "testing_requirement_level": testing_requirement_level.value if hasattr(testing_requirement_level, "value") else str(testing_requirement_level),
        "testing_multiplier": testing_mult,
        "vendor_dependency_count": vendor_dependency_count,
        "vendor_dependency_multiplier": round(vendor_dep_mult, 2),
        "pki_cert_dependency_count": pki_cert_dependency_count,
        "pki_cert_multiplier": round(pki_cert_mult, 2),
        "business_criticality_score": business_criticality_score,
        "engineering_capacity_developers": dev_capacity,
        "parallel_efficiency": round(parallel_efficiency, 2),
        "vendor_lead_time_months_buffer": vendor_lead_time_months
    }

    return {
        "person_days": total_person_days,
        "person_months": total_person_months,
        "calendar_months": calendar_months,
        "assumptions": assumptions
    }
