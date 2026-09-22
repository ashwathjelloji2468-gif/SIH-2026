from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.qars.migration_calibration import load_migration_calibration


class QARSMigrationComplexity(BaseModel):
    """
    Phase 4 Migration Complexity evaluation result.
    """
    score: Optional[float] = Field(None, description="Normalized MC score [0, 100] or None if UNCONFIGURED")
    status: str = Field(..., description="CONFIGURED | PARTIALLY_CONFIGURED | UNCONFIGURED")
    factors: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, str] = Field(default_factory=dict)
    missing_factors: List[str] = Field(default_factory=list)
    contributing_factors: Dict[str, float] = Field(default_factory=dict)
    confidence: str = "PROVISIONAL"
    calibration_version: str = "SENTRIQ QARS Prototype Heuristic Migration Calibration v1"
    explanation: str = ""


def collect_migration_complexity_evidence(
    asset: Any,
    project: Optional[Any] = None,
    db: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Collects real observable migration complexity evidence and provenance mapping.
    Does NOT use legacy effort_estimator defaults (4.0, 0.5, 75.0).
    """
    factors: Dict[str, Any] = {}
    provenance: Dict[str, str] = {}
    missing_factors: List[str] = []

    extra = dict(getattr(asset, "extra_metadata", {}) or {}) if hasattr(asset, "extra_metadata") else (asset.get("extra_metadata", {}) if isinstance(asset, dict) else {})
    overrides = extra.get("context_overrides", {})

    # 1. Affected Files Count
    files_count = 1
    if hasattr(asset, "evidence_items") and asset.evidence_items:
        files_set = {e.source_file for e in asset.evidence_items if hasattr(e, "source_file") and e.source_file}
        if files_set:
            files_count = len(files_set)
    factors["affected_files_count"] = files_count
    provenance["affected_files_count"] = "SCANNER_EVIDENCE"

    # 2. Affected Assets Count
    assets_count = 1
    if hasattr(asset, "scan") and asset.scan and hasattr(asset.scan, "assets"):
        assets_count = max(1, len(asset.scan.assets))
    factors["affected_assets_count"] = assets_count
    provenance["affected_assets_count"] = "SCANNER_EVIDENCE"

    # 3. Dependency Count
    dep_count = 0
    if hasattr(asset, "scan") and asset.scan and hasattr(asset.scan, "edges"):
        dep_count = sum(
            1 for edge in asset.scan.edges
            if hasattr(edge, "relation_type") and str(edge.relation_type).lower() in ["depends_on", "uses"]
        )
    factors["dependency_count"] = dep_count
    provenance["dependency_count"] = "SCANNER_EVIDENCE"

    # 4. Protocol Impact Detected
    alg_str = str(getattr(asset, "algorithm_name", "") or extra.get("algorithm", "")).upper()
    asset_type_str = str(getattr(asset, "asset_type", "") or extra.get("asset_type", "")).upper()
    purpose_str = str(getattr(asset, "purpose", "") or extra.get("purpose", "")).upper()
    proto = ("PROTOCOL" in asset_type_str or "TLS" in alg_str or "SSH" in alg_str or "KEY_ESTABLISHMENT" in purpose_str)
    factors["protocol_impact_detected"] = proto
    provenance["protocol_impact_detected"] = "SCANNER_EVIDENCE"

    # 5. Vendor / KMS / HSM Detected
    vendor_kms = ("VENDOR" in asset_type_str or "BINARY" in asset_type_str or "KMS" in alg_str or "HSM" in alg_str)
    factors["vendor_kms_hsm_detected"] = vendor_kms
    provenance["vendor_kms_hsm_detected"] = "SCANNER_EVIDENCE"

    # 6. Blast Radius Affected Nodes
    blast_nodes = 0
    if "blast_radius_affected_nodes" in extra and extra["blast_radius_affected_nodes"] is not None:
        blast_nodes = int(extra["blast_radius_affected_nodes"])
    elif hasattr(asset, "scan") and asset.scan and hasattr(asset.scan, "blast_radius_results") and asset.scan.blast_radius_results:
        blast_nodes = int(asset.scan.blast_radius_results[0].affected_nodes_count)
    factors["blast_radius_affected_nodes"] = blast_nodes
    provenance["blast_radius_affected_nodes"] = "DERIVED_SYSTEM_ANALYSIS"

    # 7. Business Criticality Score
    crit_score = None
    if "business_criticality_score" in overrides:
        crit_score = float(overrides["business_criticality_score"])
        provenance["business_criticality_score"] = "USER_OVERRIDE"
    elif "business_criticality_score" in extra:
        crit_score = float(extra["business_criticality_score"])
        provenance["business_criticality_score"] = "PROJECT_BUSINESS_CONTEXT"
    elif project and hasattr(project, "business_context") and isinstance(project.business_context, dict):
        if "criticality_score" in project.business_context:
            crit_score = float(project.business_context["criticality_score"])
            provenance["business_criticality_score"] = "PROJECT_BUSINESS_CONTEXT"

    if crit_score is not None:
        factors["business_criticality_score"] = crit_score
    else:
        missing_factors.append("business_criticality_score")

    # 8. Testing Requirement Level
    test_req = None
    if "testing_requirement_level" in overrides:
        test_req = str(overrides["testing_requirement_level"])
        provenance["testing_requirement_level"] = "USER_OVERRIDE"
    elif "testing_requirement_level" in extra:
        test_req = str(extra["testing_requirement_level"])
        provenance["testing_requirement_level"] = "PROJECT_BUSINESS_CONTEXT"

    if test_req:
        factors["testing_requirement_level"] = test_req
    else:
        missing_factors.append("testing_requirement_level")

    # Missing factors check
    missing_sources = [
        "downtime_financial_cost_per_hour",
        "sla_availability_target_percentage",
        "active_user_operations_impact_count",
        "external_service_topology"
    ]
    missing_factors.extend(missing_sources)

    return {
        "factors": factors,
        "provenance": provenance,
        "missing_factors": missing_factors
    }


def evaluate_migration_complexity(
    asset: Any,
    project: Optional[Any] = None,
    db: Optional[Any] = None
) -> QARSMigrationComplexity:
    """
    Evaluates Migration Complexity (MC in [0, 100]) deterministically using qars_migration_calibration.json dataset.
    Renormalizes strictly across configured factors without fabricating values for missing factors.
    """
    evidence_data = collect_migration_complexity_evidence(asset, project=project, db=db)
    factors = evidence_data["factors"]
    provenance = evidence_data["provenance"]
    missing_factors = evidence_data["missing_factors"]

    calib = load_migration_calibration()
    version = calib.get("metadata", {}).get("version", "SENTRIQ QARS Prototype Heuristic Migration Calibration v1")
    weights = calib.get("factor_weights", {})
    max_bounds = calib.get("max_bounds", {})

    contributing_factors: Dict[str, float] = {}
    weighted_sum = 0.0
    active_weight_sum = 0.0

    for factor_key, weight in weights.items():
        if factor_key in factors and factors[factor_key] is not None:
            val = factors[factor_key]
            norm_val = 0.0

            if isinstance(val, bool):
                norm_val = 1.0 if val else 0.0
            elif isinstance(val, (int, float)):
                bound = max_bounds.get(factor_key, 100.0)
                norm_val = min(1.0, float(val) / float(bound))
            elif isinstance(val, str):
                if val.upper() in ["REGULATED", "CRITICAL"]:
                    norm_val = 1.0
                elif val.upper() in ["HIGH"]:
                    norm_val = 0.75
                elif val.upper() in ["MEDIUM"]:
                    norm_val = 0.50
                else:
                    norm_val = 0.25

            factor_contrib = norm_val * weight * 100.0
            contributing_factors[factor_key] = round(factor_contrib, 2)
            weighted_sum += norm_val * weight
            active_weight_sum += weight

    if active_weight_sum > 0:
        mc_score = round((weighted_sum / active_weight_sum) * 100.0, 2)
        status = "CONFIGURED" if len(missing_factors) == 4 else "PARTIALLY_CONFIGURED"
    else:
        mc_score = None
        status = "UNCONFIGURED"

    explanation = (
        f"Migration Complexity assessed at {mc_score}/100 based on {len(contributing_factors)} active evidence factors."
        if mc_score is not None
        else "Migration Complexity unconfigured due to missing runtime evidence."
    )

    return QARSMigrationComplexity(
        score=mc_score,
        status=status,
        factors=factors,
        provenance=provenance,
        missing_factors=missing_factors,
        contributing_factors=contributing_factors,
        confidence="PROVISIONAL",
        calibration_version=version,
        explanation=explanation
    )
