from typing import Dict, Any, List, Optional
from app.models.enums import TestingRequirement

def classify_migration_effort(
    affected_assets_count: int,
    affected_files_count: int = 1,
    blast_radius_affected_nodes: int = 0,
    blast_radius_score: Optional[float] = None,
    vendor_dependency_count: int = 0,
    pki_cert_dependency_count: int = 0,
    business_criticality_score: float = 50.0,
    vendor_kms_hsm_detected: bool = False,
    protocol_impact_detected: bool = False,
    testing_requirement_level: Any = TestingRequirement.HIGH
) -> Dict[str, Any]:
    """
    Evidence-backed Migration Effort Classifier for SENTRIQ (Priority 7).
    Classifies migration effort into LOW, MEDIUM, or HIGH based strictly on
    observable project evidence and explainable factors.
    """
    evidence_factors: List[str] = []

    # 1. Observable Scope Factors
    if affected_assets_count > 0:
        evidence_factors.append(f"{affected_assets_count} cryptographic asset(s) identified")
    if affected_files_count > 1:
        evidence_factors.append(f"{affected_files_count} source/config file(s) affected")

    # 2. Blast Radius Signals (Priority 6)
    if blast_radius_affected_nodes > 0:
        evidence_factors.append(f"{blast_radius_affected_nodes} dependent node(s) affected in blast radius")
    if blast_radius_score is not None and blast_radius_score >= 50.0:
        evidence_factors.append(f"Elevated blast radius impact score ({blast_radius_score:.1f}/100)")

    # 3. Infrastructure & Vendor Dependencies (Priority 5)
    if vendor_kms_hsm_detected or vendor_dependency_count > 0:
        count_str = f" ({vendor_dependency_count} integration(s))" if vendor_dependency_count > 0 else ""
        evidence_factors.append(f"Hardware HSM / Cloud KMS / Vendor dependency detected{count_str}")

    # 4. Protocol & PKI Certificate Impact (Priority 5)
    if protocol_impact_detected or pki_cert_dependency_count > 0:
        count_str = f" ({pki_cert_dependency_count} cert chain(s))" if pki_cert_dependency_count > 0 else ""
        evidence_factors.append(f"Protocol (TLS/SSH) or PKI certificate store update required{count_str}")

    # 5. Business Criticality Context (Priority 3)
    crit_level_str = "CRITICAL" if business_criticality_score >= 80.0 else "HIGH" if business_criticality_score >= 60.0 else "MEDIUM"
    if business_criticality_score >= 60.0:
        evidence_factors.append(f"Business system criticality assessed at {crit_level_str} ({business_criticality_score:.0f}/100)")

    # 6. Testing & Validation Overhead (Priority 2)
    req_val = testing_requirement_level.value if hasattr(testing_requirement_level, "value") else str(testing_requirement_level)
    if req_val in ["REGULATED", "HIGH"]:
        evidence_factors.append(f"Validation testing requirement level: {req_val}")

    if not evidence_factors:
        evidence_factors.append("Standard single-component crypto asset update")

    # Classification Rules (Explainable & Deterministic)
    is_high = (
        affected_assets_count >= 10 or
        blast_radius_affected_nodes >= 10 or
        vendor_kms_hsm_detected or
        vendor_dependency_count >= 2 or
        business_criticality_score >= 85.0 or
        (protocol_impact_detected and pki_cert_dependency_count >= 2) or
        req_val == "REGULATED"
    )

    is_medium = (
        affected_assets_count >= 3 or
        blast_radius_affected_nodes >= 3 or
        business_criticality_score >= 60.0 or
        vendor_dependency_count >= 1 or
        pki_cert_dependency_count >= 1 or
        protocol_impact_detected
    )

    if is_high:
        effort_level = "HIGH"
    elif is_medium:
        effort_level = "MEDIUM"
    else:
        effort_level = "LOW"

    return {
        "effort_level": effort_level,
        "evidence_factors": evidence_factors
    }

def estimate_migration_effort(
    affected_assets_count: int,
    affected_files_count: int = 1,
    blast_radius_affected_nodes: int = 0,
    blast_radius_score: Optional[float] = None,
    affected_apps_count: int = 1,
    dependency_count: int = 0,
    vendor_dependency_count: int = 1,
    pki_cert_dependency_count: int = 1,
    crypto_agility_score: float = 0.5,
    testing_requirement_level: Any = TestingRequirement.HIGH,
    business_criticality_score: float = 75.0,
    engineering_capacity_developers: int = 3,
    vendor_kms_hsm_detected: bool = False,
    protocol_impact_detected: bool = False
) -> Dict[str, Any]:
    """
    Estimates migration effort and evidence-backed classification for SENTRIQ.
    Returns effort_level ('LOW', 'MEDIUM', 'HIGH'), evidence_factors, and capacity planning numbers.
    """
    classification = classify_migration_effort(
        affected_assets_count=affected_assets_count,
        affected_files_count=affected_files_count,
        blast_radius_affected_nodes=blast_radius_affected_nodes,
        blast_radius_score=blast_radius_score,
        vendor_dependency_count=vendor_dependency_count,
        pki_cert_dependency_count=pki_cert_dependency_count,
        business_criticality_score=business_criticality_score,
        vendor_kms_hsm_detected=vendor_kms_hsm_detected,
        protocol_impact_detected=protocol_impact_detected,
        testing_requirement_level=testing_requirement_level
    )

    base_days_per_asset = 4.0
    agility_factor = max(0.6, 1.5 - (crypto_agility_score * 0.8))

    testing_multipliers = {
        TestingRequirement.LOW: 1.0,
        TestingRequirement.MEDIUM: 1.2,
        TestingRequirement.HIGH: 1.5,
        TestingRequirement.REGULATED: 1.9
    }
    t_level = testing_requirement_level if isinstance(testing_requirement_level, TestingRequirement) else TestingRequirement.HIGH
    testing_mult = testing_multipliers.get(t_level, 1.5)

    vendor_dep_mult = 1.0 + (0.35 * vendor_dependency_count)
    pki_cert_mult = 1.0 + (0.25 * pki_cert_dependency_count)
    criticality_mult = 1.0 + (0.003 * business_criticality_score)

    asset_days = affected_assets_count * base_days_per_asset * agility_factor
    app_coordination_days = (affected_apps_count - 1) * 6.0

    total_person_days = (asset_days + app_coordination_days) * testing_mult * vendor_dep_mult * pki_cert_mult * criticality_mult
    total_person_days = round(total_person_days, 1)
    total_person_months = round(total_person_days / 20.0, 1)

    dev_capacity = max(1, engineering_capacity_developers)
    parallel_efficiency = min(0.9, 0.5 + (0.1 * dev_capacity))
    
    base_calendar_months = total_person_days / (dev_capacity * 20.0 * parallel_efficiency)
    vendor_lead_time_months = vendor_dependency_count * 1.5
    calendar_months = round(base_calendar_months + vendor_lead_time_months, 1)
    calendar_months = max(0.5, calendar_months)

    assumptions = {
        "effort_level": classification["effort_level"],
        "evidence_factors": classification["evidence_factors"],
        "affected_assets_count": affected_assets_count,
        "affected_files_count": affected_files_count,
        "blast_radius_affected_nodes": blast_radius_affected_nodes,
        "blast_radius_score": blast_radius_score,
        "vendor_dependency_count": vendor_dependency_count,
        "pki_cert_dependency_count": pki_cert_dependency_count,
        "business_criticality_score": business_criticality_score,
        "engineering_capacity_developers": dev_capacity,
        "testing_requirement_level": t_level.value if hasattr(t_level, "value") else str(t_level)
    }

    return {
        "effort_level": classification["effort_level"],
        "evidence_factors": classification["evidence_factors"],
        "factors": classification["evidence_factors"],
        "person_days": total_person_days,
        "person_months": total_person_months,
        "calendar_months": calendar_months,
        "assumptions": assumptions
    }
