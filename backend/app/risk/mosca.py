from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.engines.x_engine import XEngine
from app.engines.y_engine import YEngine
from app.engines.z_engine import ZEngine
from app.engines.mosca_engine import MoscaEngine


def estimate_migration_time_from_stats(
    total_assets: int = 0,
    total_rsa_ecc_assets: int = 0,
    hardcoded_crypto_instances: int = 0,
    legacy_ciphers_count: int = 0,
    has_vendor_managed_or_hsm: bool = False,
    total_files_scanned: int = 0
) -> float:
    """Delegate Y estimation to canonical YEngine (MVP default STANDARD: 10 years)."""
    return float(YEngine().evaluate_y()["value"])


def estimate_migration_time_from_assets(assets: List[Any] = None) -> float:
    """Delegate Y estimation to canonical YEngine (MVP default STANDARD: 10 years)."""
    return float(YEngine().evaluate_y()["value"])


def build_dynamic_mosca_inputs(
    asset_or_assets: Any = None,
    explicit_data_lifetime_years: Optional[float] = None,
    explicit_migration_time_years: Optional[float] = None,
    quantum_threat_horizon_year: Optional[int] = None
) -> Tuple[float, float, int]:
    """Build canonical (X, Y, Z) inputs using canonical X, Y, Z engines."""
    if explicit_data_lifetime_years is not None:
        x = float(explicit_data_lifetime_years)
    elif asset_or_assets and not isinstance(asset_or_assets, list) and getattr(asset_or_assets, "data_lifetime_years", None) is not None:
        x = float(getattr(asset_or_assets, "data_lifetime_years"))
    elif isinstance(asset_or_assets, list) and len(asset_or_assets) > 0:
        x_vals = [float(getattr(a, "data_lifetime_years", None)) for a in asset_or_assets if getattr(a, "data_lifetime_years", None) is not None]
        x = max(x_vals) if x_vals else float(XEngine().evaluate_x()["value"])
    else:
        x = float(XEngine().evaluate_x()["value"])

    y = float(explicit_migration_time_years) if explicit_migration_time_years is not None else float(YEngine().evaluate_y()["value"])

    if quantum_threat_horizon_year is not None:
        z_year = int(quantum_threat_horizon_year)
    else:
        z_year = 2036

    return x, y, z_year


def calculate_mosca_analysis(
    data_lifetime_years: Optional[float] = None,       # X
    migration_time_years: Optional[float] = None,      # Y
    quantum_threat_horizon_year: Optional[int] = None, # Z
    current_year: Optional[int] = None
) -> Dict[str, Any]:
    """Mosca's Theorem Calculation M_i = X + Y - Z_i.

    Delegates to canonical XEngine, YEngine, and ZEngine.
    """
    x_val = float(data_lifetime_years) if data_lifetime_years is not None else float(XEngine().evaluate_x()["value"])
    y_val = float(migration_time_years) if migration_time_years is not None else float(YEngine().evaluate_y()["value"])

    if current_year is None:
        current_year = 2026

    protection_window = x_val + y_val

    if quantum_threat_horizon_year is not None:
        z_years = float(quantum_threat_horizon_year - current_year)
        target_horizon_year = int(quantum_threat_horizon_year)
    else:
        z_years = 10.0
        target_horizon_year = int(current_year + z_years)

    urgency_gap = protection_window - z_years  # M_i = X + Y - Z_i

    if urgency_gap > 5.0:
        mosca_score = 100.0
        mosca_status = "DEADLINE_RISK"
        rationale = (
            f"DEADLINE RISK: Protection window X+Y ({x_val:.1f}y + {y_val:.1f}y = {protection_window:.1f}y) "
            f"severely exceeds remaining threat horizon Z ({z_years:.1f}y) by {urgency_gap:.1f} years."
        )
    elif urgency_gap > 0.0:
        mosca_score = 80.0
        mosca_status = "MIGRATION_REQUIRED"
        rationale = (
            f"MIGRATION REQUIRED: Protection window X+Y ({protection_window:.1f}y) exceeds threat horizon Z ({z_years:.1f}y). "
            f"Migration must begin immediately."
        )
    elif urgency_gap >= -5.0:
        mosca_score = 50.0
        mosca_status = "MIGRATION_REQUIRED"
        rationale = (
            f"MIGRATION REQUIRED: Protection window ({protection_window:.1f}y) approaches threat horizon ({z_years:.1f}y). "
            f"Margin is narrow ({abs(urgency_gap):.1f}y remaining)."
        )
    else:
        mosca_score = 20.0
        mosca_status = "SAFE_MARGIN"
        rationale = (
            f"SAFE MARGIN: Protection window ({protection_window:.1f}y) completes comfortably within threat horizon Z ({z_years:.1f}y)."
        )

    return {
        "mosca_score": mosca_score,
        "mosca_status": mosca_status,
        "urgency_gap_years": urgency_gap,
        "quantum_threat_horizon": target_horizon_year,
        "years_until_quantum": z_years,
        "data_lifetime_years": x_val,
        "migration_time_years": y_val,
        "protection_window_years": protection_window,
        "rationale": rationale
    }


def calculate_mosca_urgency(
    data_lifetime_years: Optional[float] = None,
    migration_time_years: Optional[float] = None,
    quantum_threat_horizon_year: Optional[int] = None,
    current_year: Optional[int] = None,
    assets: Optional[List[Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Calculate Mosca Urgency using canonical Mosca analysis."""
    res = calculate_mosca_analysis(
        data_lifetime_years=data_lifetime_years,
        migration_time_years=migration_time_years,
        quantum_threat_horizon_year=quantum_threat_horizon_year,
        current_year=current_year
    )
    res["urgency_level"] = "CRITICAL" if res["mosca_score"] >= 80.0 else ("HIGH" if res["mosca_score"] >= 50.0 else "LOW")
    return res

