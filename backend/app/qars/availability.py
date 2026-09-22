from typing import Optional, Dict, Any, List
from app.qars.models import QARSAvailability, QARSValidationError
from app.services.business_criticality_service import DEFAULT_RATINGS


def evaluate_availability(
    asset: Any,
    project: Optional[Any] = None,
    db: Optional[Any] = None,
    availability_impact_override: Optional[float] = None
) -> QARSAvailability:
    """
    Phase 3A Availability Scoring Engine.
    Primary authoritative input: project.business_context["factor_ratings"]["availabilityImpact"] (1..5).
    Normalization: AV_base = (availabilityImpact - 1) / 4 in [0, 1].
    Provenance: USER_OVERRIDE | APPLICATION_DEFAULT.
    Exposes secondary blast radius evidence without weight fabrication.
    Tracks missing availability sources explicitly.
    """
    raw_val: Optional[float] = None
    provenance: str = "APPLICATION_DEFAULT"

    # 1. Explicit override check (e.g. direct test or unit override)
    if availability_impact_override is not None:
        raw_val = float(availability_impact_override)
        provenance = "USER_OVERRIDE"

    # 2. Project factor ratings check
    if raw_val is None and project:
        bctx = dict(getattr(project, "business_context", {}) or {}) if hasattr(project, "business_context") else (project.get("business_context", {}) if isinstance(project, dict) else {})
        ratings = bctx.get("factor_ratings")
        if isinstance(ratings, dict) and "availabilityImpact" in ratings and ratings["availabilityImpact"] is not None:
            try:
                raw_val = float(ratings["availabilityImpact"])
                provenance = "USER_OVERRIDE"
            except (ValueError, TypeError):
                pass

    # 3. Application default fallback
    if raw_val is None:
        def_impact = DEFAULT_RATINGS.get("availabilityImpact", 4)
        raw_val = float(def_impact)
        provenance = "APPLICATION_DEFAULT"

    # 4. Validation
    if raw_val < 1.0 or raw_val > 5.0:
        raise QARSValidationError(
            f"Invalid availabilityImpact rating ({raw_val}). Must be in range [1.0, 5.0]."
        )

    # 5. Score calculation: AV_base = (availabilityImpact - 1) / 4
    av_base = min(1.0, max(0.0, (raw_val - 1.0) / 4.0))

    # 6. Collect secondary unweighted evidence
    evidence: Dict[str, Any] = {}
    extra = dict(getattr(asset, "extra_metadata", {}) or {}) if hasattr(asset, "extra_metadata") else (asset.get("extra_metadata", {}) if isinstance(asset, dict) else {})
    if "blast_radius_score" in extra and extra["blast_radius_score"] is not None:
        evidence["blast_radius_score"] = float(extra["blast_radius_score"])
    if "affected_nodes_count" in extra and extra["affected_nodes_count"] is not None:
        evidence["affected_nodes_count"] = int(extra["affected_nodes_count"])

    # Check database relationships if asset model instance has blast_radius_results
    if not evidence and hasattr(asset, "scan") and asset.scan and hasattr(asset.scan, "blast_radius_results"):
        br_items = asset.scan.blast_radius_results
        if br_items:
            evidence["blast_radius_score"] = float(br_items[0].radius_score)
            evidence["affected_nodes_count"] = int(br_items[0].affected_nodes_count)

    # 7. Explicit missing sources
    missing_factors = [
        "downtime_financial_cost_per_hour",
        "sla_availability_target_percentage",
        "active_user_operations_impact_count",
        "external_service_topology"
    ]

    explanation = (
        f"AV score {av_base:.4f} calculated from availabilityImpact rating {raw_val:.1f}/5 "
        f"via AV_base = (availabilityImpact - 1) / 4."
    )

    return QARSAvailability(
        score=av_base,
        raw_rating=raw_val,
        provenance=provenance,
        status="CONFIGURED",
        missing_factors=missing_factors,
        evidence=evidence,
        explanation=explanation
    )
