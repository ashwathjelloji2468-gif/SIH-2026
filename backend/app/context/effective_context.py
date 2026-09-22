import os
from typing import Dict, Any, Optional
from app.engines.x_engine import XEngine
from app.services.business_criticality_service import DEFAULT_RATINGS

def resolve_effective_artifact_context(
    asset: Any,
    project: Optional[Any] = None,
    db: Optional[Any] = None,
    precomputed_business_context: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Canonical Context Resolver for Cryptographic Artifacts.
    
    Precedence:
    1. Valid artifact-specific override (asset.extra_metadata["context_overrides"]) -> ARTIFACT_EVIDENCE
    2. Explicit user override (Project / folder settings) -> USER_OVERRIDE
    3. Application/project level default -> APPLICATION_DEFAULT
    """
    bctx = dict(getattr(project, "business_context", {}) or {}) if project else {}
    raw_ratings = bctx.get("factor_ratings")
    ratings = raw_ratings if isinstance(raw_ratings, dict) and len(raw_ratings) > 0 else DEFAULT_RATINGS

    # 1. Application defaults from DEFAULT_RATINGS
    app_data_sens = ratings.get("dataSensitivity", DEFAULT_RATINGS["dataSensitivity"])
    app_reg_impact = ratings.get("regulatoryExposure", DEFAULT_RATINGS["regulatoryExposure"])
    app_fin_impact = ratings.get("financialImpact", DEFAULT_RATINGS["financialImpact"])
    app_ops_impact = max(
        ratings.get("availabilityImpact", DEFAULT_RATINGS["availabilityImpact"]),
        ratings.get("integrityImpact", DEFAULT_RATINGS["integrityImpact"])
    )

    # Exposure rating default mapping (4 or 5 -> EXTERNAL_FACING, else INTERNAL)
    raw_exp = ratings.get("exposureRating", DEFAULT_RATINGS["exposureRating"])
    if isinstance(raw_exp, str):
        app_exposure = "EXTERNAL_FACING" if "EXTERNAL" in raw_exp.upper() else "INTERNAL"
    else:
        app_exposure = "EXTERNAL_FACING" if raw_exp >= 4 else "INTERNAL"

    # Business Criticality App Default
    app_bus_crit = "UNKNOWN"
    bus_crit_source = "APPLICATION_DEFAULT"
    if bctx.get("user_override") in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        app_bus_crit = bctx.get("user_override")
        bus_crit_source = "USER_OVERRIDE"
    elif precomputed_business_context is not None:
        if isinstance(precomputed_business_context, dict):
            app_bus_crit = (
                precomputed_business_context.get("effective_criticality")
                or precomputed_business_context.get("user_override")
                or getattr(asset, "business_criticality_label", None)
                or "UNKNOWN"
            )
        elif isinstance(precomputed_business_context, str):
            app_bus_crit = precomputed_business_context
        else:
            app_bus_crit = getattr(asset, "business_criticality_label", None) or "UNKNOWN"
    elif project and db:
        try:
            from app.services.business_criticality_service import BusinessCriticalityService
            srv = BusinessCriticalityService(db)
            res = srv.get_project_business_criticality(project.id)
            app_bus_crit = res.get("effective_criticality") or getattr(asset, "business_criticality_label", None) or "UNKNOWN"
        except Exception:
            app_bus_crit = getattr(asset, "business_criticality_label", None) or "UNKNOWN"
    else:
        app_bus_crit = getattr(asset, "business_criticality_label", None) or "UNKNOWN"

    # Extract artifact context_overrides
    extra = dict(getattr(asset, "extra_metadata", {}) or {})
    overrides = extra.get("context_overrides") or {}
    if not isinstance(overrides, dict):
        overrides = {}

    # Initialize results dictionary
    sources = {}

    # --- Field 1: X Years ---
    art_x = overrides.get("x_years")
    if art_x is not None and isinstance(art_x, (int, float)) and art_x > 0:
        eff_x = float(art_x)
        sources["x_years"] = "ARTIFACT_EVIDENCE"
    else:
        user_x = getattr(project, "user_x_years", None) if project else None
        user_domain = getattr(project, "user_domain", None) if project else None
        proj_name = getattr(project, "name", None) if project else None
        proj_desc = getattr(project, "description", None) if project else None
        repo_url = getattr(project, "repository_url", None) if project else None
        folder_contexts = getattr(project, "folder_contexts", None) if project else None
        asset_loc = getattr(asset, "location", None)

        x_res = XEngine().evaluate_x(
            user_x_years=user_x,
            user_domain=user_domain,
            project_name=proj_name,
            description=proj_desc,
            repository_url=repo_url,
            folder_path=asset_loc,
            folder_contexts=folder_contexts
        )
        eff_x = float(x_res["value"])
        if x_res.get("source") == "USER":
            sources["x_years"] = "USER_OVERRIDE"
        else:
            sources["x_years"] = "APPLICATION_DEFAULT"

    # --- Field 2: Data Sensitivity ---
    art_ds = overrides.get("data_sensitivity")
    if art_ds is not None and isinstance(art_ds, (int, float)) and 1 <= art_ds <= 5:
        eff_ds = int(art_ds)
        sources["data_sensitivity"] = "ARTIFACT_EVIDENCE"
    else:
        eff_ds = int(app_data_sens)
        sources["data_sensitivity"] = "APPLICATION_DEFAULT"

    # --- Field 3: Business Criticality ---
    art_bc = overrides.get("business_criticality")
    if art_bc is not None:
        if isinstance(art_bc, str) and art_bc.upper() in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            eff_bc = art_bc.upper()
            sources["business_criticality"] = "ARTIFACT_EVIDENCE"
        elif isinstance(art_bc, (int, float)):
            val_map = {1: "LOW", 2: "LOW", 3: "MEDIUM", 4: "HIGH", 5: "CRITICAL"}
            eff_bc = val_map.get(int(art_bc), "MEDIUM")
            sources["business_criticality"] = "ARTIFACT_EVIDENCE"
        else:
            eff_bc = app_bus_crit
            sources["business_criticality"] = bus_crit_source
    else:
        eff_bc = app_bus_crit
        sources["business_criticality"] = bus_crit_source

    # --- Field 4: Regulatory Impact ---
    art_reg = overrides.get("regulatory_impact")
    if art_reg is not None and isinstance(art_reg, (int, float)) and 1 <= art_reg <= 5:
        eff_reg = int(art_reg)
        sources["regulatory_impact"] = "ARTIFACT_EVIDENCE"
    else:
        eff_reg = int(app_reg_impact)
        sources["regulatory_impact"] = "APPLICATION_DEFAULT"

    # --- Field 5: Financial Impact ---
    art_fin = overrides.get("financial_impact")
    if art_fin is not None and isinstance(art_fin, (int, float)) and 1 <= art_fin <= 5:
        eff_fin = int(art_fin)
        sources["financial_impact"] = "ARTIFACT_EVIDENCE"
    else:
        eff_fin = int(app_fin_impact)
        sources["financial_impact"] = "APPLICATION_DEFAULT"

    # --- Field 6: Operational Impact ---
    art_ops = overrides.get("operational_impact")
    if art_ops is not None and isinstance(art_ops, (int, float)) and 1 <= art_ops <= 5:
        eff_ops = int(art_ops)
        sources["operational_impact"] = "ARTIFACT_EVIDENCE"
    else:
        eff_ops = int(app_ops_impact)
        sources["operational_impact"] = "APPLICATION_DEFAULT"

    # --- Field 7: Exposure ---
    art_exp = overrides.get("exposure")
    if art_exp is not None and isinstance(art_exp, str) and art_exp.upper() in ["INTERNAL", "EXTERNAL_FACING", "EXTERNAL"]:
        norm_exp = "EXTERNAL_FACING" if "EXTERNAL" in art_exp.upper() else "INTERNAL"
        eff_exp = norm_exp
        sources["exposure"] = "ARTIFACT_EVIDENCE"
    else:
        eff_exp = app_exposure
        sources["exposure"] = "APPLICATION_DEFAULT"

    resolved_context = {
        "x_years": eff_x,
        "data_sensitivity": eff_ds,
        "business_criticality": eff_bc,
        "regulatory_impact": eff_reg,
        "financial_impact": eff_fin,
        "operational_impact": eff_ops,
        "exposure": eff_exp,
        "sources": sources
    }

    # Safely merge into extra_metadata["effective_context"] if asset supports metadata mutation
    if hasattr(asset, "extra_metadata"):
        if extra.get("effective_context") != resolved_context:
            extra["effective_context"] = resolved_context
            asset.extra_metadata = extra

    return resolved_context
