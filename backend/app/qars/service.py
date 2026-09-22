from typing import Optional, Dict, Any
from app.context.effective_context import resolve_effective_artifact_context
from app.engines.y_engine import YEngine
from app.engines.z_engine import ZEngine
from app.qars.models import (
    QARSCoreInput,
    QARSValidationError,
    QARSProvenance,
    QARSRuntimeResult,
    QARSPolicyInput,
)
from app.qars.core import compute_qars_core
from app.qars.policy import QARSPolicyEngine, ComponentProvider
from app.qars.config import QARSConfig
from app.qars.algorithm import evaluate_algorithm_risk
from app.qars.availability import evaluate_availability
from app.qars.agility import collect_crypto_agility_evidence
from app.qars.migration import evaluate_migration_complexity
from app.qars.uncertainty import evaluate_z_uncertainty


def evaluate_artifact_qars(
    asset: Any,
    project: Optional[Any] = None,
    db: Optional[Any] = None,
    config: Optional[QARSConfig] = None,
    provider: Optional[ComponentProvider] = None,
) -> QARSRuntimeResult:
    """
    Orchestration service connecting QARS Core & Policy engine to real SENTRIQ runtime context.
    Resolves artifact-level canonical inputs:
    - X, S, E from effective artifact context
    - Y from YEngine
    - Z from ZEngine
    - Phase 2 Algorithm Risk & Security Objectives
    - Phase 3A Availability & Crypto-Agility Evidence
    - Phase 4 Migration Complexity Evidence & Calibration
    - Phase 4 Z Uncertainty Contract
    Preserves exact provenance metadata and fails deterministically if required inputs cannot be resolved.
    """
    # 1. Resolve Asset, Project, and Scan Identity
    asset_id = str(
        getattr(asset, "id", None)
        or (asset.get("id") if isinstance(asset, dict) else None)
        or "unknown-asset"
    )
    project_id = (
        getattr(project, "id", None)
        or (project.get("id") if isinstance(project, dict) else None)
        or (getattr(asset, "project_id", None) if hasattr(asset, "project_id") else None)
        or (asset.get("project_id") if isinstance(asset, dict) else None)
    )
    scan_id = (
        getattr(asset, "scan_id", None)
        if hasattr(asset, "scan_id")
        else (asset.get("scan_id") if isinstance(asset, dict) else None)
    )

    # 2. Resolve Effective Artifact Context (X, S, E)
    eff_ctx = resolve_effective_artifact_context(asset, project, db)

    raw_x = eff_ctx.get("x_years")
    if raw_x is None or not isinstance(raw_x, (int, float)) or raw_x <= 0:
        raise QARSValidationError(
            f"Missing or invalid required runtime input 'x_years' (X) for asset '{asset_id}' "
            f"in project '{project_id}'. Expected source: effective artifact context / XEngine. Got: {raw_x}"
        )
    x_val = float(raw_x)
    x_source = eff_ctx.get("sources", {}).get("x_years", "APPLICATION_DEFAULT")

    raw_s = eff_ctx.get("data_sensitivity")
    if raw_s is None or not isinstance(raw_s, (int, float)) or raw_s < 1.0 or raw_s > 5.0:
        raise QARSValidationError(
            f"Missing or invalid required runtime input 'data_sensitivity' (S) for asset '{asset_id}' "
            f"in project '{project_id}'. Expected source: effective artifact context (1..5). Got: {raw_s}"
        )
    s_val = float(raw_s)
    s_source = eff_ctx.get("sources", {}).get("data_sensitivity", "APPLICATION_DEFAULT")

    extra = dict(getattr(asset, "extra_metadata", {}) or {}) if hasattr(asset, "extra_metadata") else (asset.get("extra_metadata", {}) if isinstance(asset, dict) else {})
    overrides = extra.get("context_overrides") or {}
    if not isinstance(overrides, dict):
        overrides = {}

    art_exp = overrides.get("exposure") or overrides.get("exposure_rating")
    if art_exp is not None and isinstance(art_exp, (int, float)) and 1 <= art_exp <= 5:
        e_val = float(art_exp)
        e_source = "ARTIFACT_EVIDENCE"
    else:
        bctx = dict(getattr(project, "business_context", {}) or {}) if project else (project.get("business_context", {}) if isinstance(project, dict) else {})
        raw_ratings = bctx.get("factor_ratings")
        if isinstance(raw_ratings, dict) and "exposureRating" in raw_ratings and isinstance(raw_ratings["exposureRating"], (int, float)) and 1 <= raw_ratings["exposureRating"] <= 5:
            e_val = float(raw_ratings["exposureRating"])
            e_source = "USER_OVERRIDE"
        else:
            from app.services.business_criticality_service import DEFAULT_RATINGS
            app_def_exp = DEFAULT_RATINGS.get("exposureRating") if isinstance(DEFAULT_RATINGS, dict) else None
            if app_def_exp is not None and isinstance(app_def_exp, (int, float)) and 1 <= app_def_exp <= 5:
                e_val = float(app_def_exp)
                e_source = "APPLICATION_DEFAULT"
            else:
                raise QARSValidationError(
                    f"Missing or invalid required runtime input 'exposure' (E) for asset '{asset_id}' "
                    f"in project '{project_id}'. Expected numeric 1..5 rating source."
                )

    if e_val < 1.0 or e_val > 5.0:
        raise QARSValidationError(
            f"Missing or invalid required runtime input 'exposure' (E) for asset '{asset_id}' "
            f"in project '{project_id}'. Expected numeric 1..5 rating source. Got: {e_val}"
        )

    # 3. Resolve Y (y_years) via YEngine
    user_y_scen = None
    if project:
        user_y_scen = getattr(project, "user_y_scenario", None) if hasattr(project, "user_y_scenario") else project.get("user_y_scenario") if isinstance(project, dict) else None

    y_res = YEngine().evaluate_y(user_scenario=user_y_scen)
    raw_y = y_res.get("value_years") or y_res.get("value")
    if raw_y is None or not isinstance(raw_y, (int, float)) or float(raw_y) < 0:
        raise QARSValidationError(
            f"Missing or invalid required runtime input 'y_years' (Y) for asset '{asset_id}' "
            f"in project '{project_id}'. Expected source: YEngine (>= 0). Got: {raw_y}"
        )
    y_val = float(raw_y)
    y_source = "USER_OVERRIDE" if y_res.get("source") == "USER_SELECTED" else "APPLICATION_DEFAULT"

    # 4. Resolve Z (z_years) via ZEngine & Z Uncertainty
    z_res = ZEngine().evaluate_asset(asset)
    raw_z = z_res.get("z_value")
    if raw_z is None:
        raw_z = z_res.get("value_years_remaining")

    if raw_z is None or not isinstance(raw_z, (int, float)) or float(raw_z) <= 0:
        raise QARSValidationError(
            f"Missing required runtime input 'z_years' (Z) for asset '{asset_id}' "
            f"in project '{project_id}'. Expected source: ZEngine (z_value > 0)."
        )
    z_val = float(raw_z)
    z_source = "Z_ENGINE"

    z_uncert = evaluate_z_uncertainty(z_res)

    # 5. Construct QARSCoreInput & Execute Core Calculation
    core_input = QARSCoreInput(
        x_years=x_val,
        y_years=y_val,
        z_years=z_val,
        data_sensitivity=s_val,
        exposure=e_val,
    )
    core_output = compute_qars_core(core_input)

    # 6. Evaluate Phase 2 Algorithm Risk if algorithm present
    alg_name = (
        getattr(asset, "algorithm", None)
        or getattr(asset, "algorithm_type", None)
        or (asset.get("algorithm") if isinstance(asset, dict) else None)
        or (asset.get("algorithm_type") if isinstance(asset, dict) else None)
    )
    key_size = (
        getattr(asset, "key_length", None)
        or getattr(asset, "key_size", None)
        or (asset.get("key_length") if isinstance(asset, dict) else None)
        or (asset.get("key_size") if isinstance(asset, dict) else None)
    )
    purpose = (
        getattr(asset, "purpose", None)
        or (asset.get("purpose") if isinstance(asset, dict) else None)
    )

    alg_risk = None
    if alg_name is not None and str(alg_name).strip():
        parsed_key_size = int(key_size) if key_size is not None and str(key_size).isdigit() else None
        alg_risk = evaluate_algorithm_risk(
            algorithm_name=str(alg_name),
            key_size=parsed_key_size,
            purpose=str(purpose) if purpose else None,
        )

    # 7. Evaluate Phase 3A/4 Availability, Crypto-Agility, and Migration Complexity
    avail_res = evaluate_availability(asset=asset, project=project, db=db)
    agility_res = collect_crypto_agility_evidence(asset=asset, project=project, db=db)
    mc_res = evaluate_migration_complexity(asset=asset, project=project, db=db)

    # 8. Pass through Policy Engine
    policy_input = QARSPolicyInput(
        core_input=core_input,
        algorithm_risk=alg_risk,
        availability=avail_res,
        crypto_agility=agility_res,
        migration_complexity=mc_res,
        z_uncertainty=z_uncert,
    )
    policy_engine = QARSPolicyEngine(config=config, provider=provider)
    policy_result = policy_engine.evaluate(core_output, policy_input=policy_input)

    # 9. Construct Provenance & Return QARSRuntimeResult
    provenance = QARSProvenance(
        x_source=x_source,
        y_source=y_source,
        z_source=z_source,
        s_source=s_source,
        e_source=e_source,
    )

    return QARSRuntimeResult(
        asset_id=asset_id,
        project_id=project_id,
        scan_id=scan_id,
        provenance=provenance,
        core_input=core_input,
        base_score=policy_result.base_score,
        adjustments=policy_result.adjustments,
        final_score=policy_result.final_score,
        level=policy_result.level,
        explanation=policy_result.explanation,
        algorithm_risk=policy_result.algorithm_risk or alg_risk,
        availability=policy_result.availability or avail_res,
        crypto_agility_evidence=policy_result.crypto_agility_evidence or agility_res,
        migration_complexity=policy_result.migration_complexity or mc_res,
        z_uncertainty=policy_result.z_uncertainty or z_uncert,
    )
