from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

try:
    from app.core.config import settings
    DEFAULT_HORIZON = getattr(settings, "DEFAULT_QUANTUM_THREAT_HORIZON", 2033)
except Exception:
    DEFAULT_HORIZON = 2033


def estimate_migration_time_from_stats(
    total_assets: int = 0,
    total_rsa_ecc_assets: int = 0,
    hardcoded_crypto_instances: int = 0,
    legacy_ciphers_count: int = 0,
    has_vendor_managed_or_hsm: bool = False,
    total_files_scanned: int = 0
) -> float:
    """Dynamically estimate migration time Y (years) based on repository cryptographic inventory statistics.

    Formula:
    - Base Y = 1.0 year (minimum setup & refactoring baseline)
    - Add +0.1y per quantum-vulnerable (RSA/ECC) asset (capped at +4.0y)
    - Add +0.05y per hardcoded key / legacy cipher instance (capped at +3.0y)
    - Add +2.5y if vendor-managed / HSM hardware is present (PKI & hardware migration complexity)
    - Add +0.5y if total_assets > 20, +1.0y if total_assets > 50, +1.5y if total_assets > 100
    - If no stats provided, defaults/falls back to 3.0 years
    - Capped between 1.0 and 15.0 years
    """
    if total_assets == 0 and total_rsa_ecc_assets == 0 and hardcoded_crypto_instances == 0 and legacy_ciphers_count == 0 and not has_vendor_managed_or_hsm:
        return 3.0

    y_est = 1.0

    # Vulnerable asymmetric crypto adds refactoring time
    y_est += min(4.0, total_rsa_ecc_assets * 0.1)

    # Hardcoded keys & legacy ciphers add cleanup effort
    y_est += min(3.0, (hardcoded_crypto_instances + legacy_ciphers_count) * 0.05)

    # Vendor-managed HSM / Cloud KMS adds hardware/PKI coordination
    if has_vendor_managed_or_hsm:
        y_est += 2.5

    # Scale with overall repository cryptographic footprint
    if total_assets > 100:
        y_est += 1.5
    elif total_assets > 50:
        y_est += 1.0
    elif total_assets > 20:
        y_est += 0.5

    return round(min(15.0, max(1.0, y_est)), 1)


def estimate_migration_time_from_assets(assets: List[Any]) -> float:
    """Extract repository statistics from a list of discovered asset objects and compute dynamic Y."""
    if not assets:
        return 3.0

    total_assets = len(assets)
    total_rsa_ecc = 0
    hardcoded_count = 0
    legacy_count = 0
    has_vendor = False

    for asset in assets:
        alg = (getattr(asset, "algorithm_name", "") or "").upper()
        atype = str(getattr(asset, "asset_type", "")).upper()
        qs = str(getattr(asset, "quantum_safety", "")).upper()

        if "RSA" in alg or "ECDSA" in alg or "ECDH" in alg or "VULNERABLE" in qs:
            total_rsa_ecc += 1

        if "HARDCODED" in alg or "SECRET" in alg:
            hardcoded_count += 1

        if any(w in alg for w in ["MD5", "SHA1", "DES", "3DES", "RC4", "SSLV3", "TLSV1.0", "TLSV1.1"]):
            legacy_count += 1

        if "VENDOR_MANAGED" in atype or "BINARY" in atype or "HSM" in alg or "KMS" in alg:
            has_vendor = True

    return estimate_migration_time_from_stats(
        total_assets=total_assets,
        total_rsa_ecc_assets=total_rsa_ecc,
        hardcoded_crypto_instances=hardcoded_count,
        legacy_ciphers_count=legacy_count,
        has_vendor_managed_or_hsm=has_vendor
    )


def build_dynamic_mosca_inputs(
    asset_or_assets: Any = None,
    explicit_data_lifetime_years: Optional[float] = None,
    explicit_migration_time_years: Optional[float] = None,
    quantum_threat_horizon_year: Optional[int] = None
) -> Tuple[float, float, int]:
    """Build dynamic (X, Y, Z) inputs for Mosca analysis based on asset/repo data.

    - X (data_lifetime): from asset classification or explicit override (default 10.0)
    - Y (migration_time): estimated dynamically from repo asset stats or explicit override (default 3.0)
    - Z (threat_horizon): project setting or default 2033
    """
    # 1. Determine X (Data Lifetime)
    x = 10.0
    if explicit_data_lifetime_years is not None:
        x = float(explicit_data_lifetime_years)
    elif asset_or_assets and not isinstance(asset_or_assets, list):
        x = float(getattr(asset_or_assets, "data_lifetime_years", 10.0) or 10.0)
    elif isinstance(asset_or_assets, list) and len(asset_or_assets) > 0:
        x_vals = [float(getattr(a, "data_lifetime_years", 10.0) or 10.0) for a in asset_or_assets]
        x = max(x_vals) if x_vals else 10.0

    # 2. Determine Y (Migration Time)
    if explicit_migration_time_years is not None:
        y = float(explicit_migration_time_years)
    elif isinstance(asset_or_assets, list):
        y = estimate_migration_time_from_assets(asset_or_assets)
    elif asset_or_assets is not None:
        y = estimate_migration_time_from_assets([asset_or_assets])
    else:
        y = 3.0

    # 3. Determine Z (Threat Horizon)
    z = quantum_threat_horizon_year or DEFAULT_HORIZON

    return x, y, z


def calculate_mosca_analysis(
    data_lifetime_years: float = 10.0,       # X
    migration_time_years: float = 3.0,        # Y
    quantum_threat_horizon_year: int = None,  # Z
    current_year: int = None
) -> Dict[str, Any]:
    """Mosca's Theorem Calculation:

    If X + Y > Z, data security is compromised before migration completes.
    - X: Required data protection lifetime (years)
    - Y: Time required to migrate infrastructure (years)
    - Z: Time until quantum threat (threat horizon)
    """
    if quantum_threat_horizon_year is None:
        quantum_threat_horizon_year = DEFAULT_HORIZON

    if current_year is None:
        current_year = datetime.now(timezone.utc).year

    years_until_quantum = max(1.0, float(quantum_threat_horizon_year - current_year))
    protection_window = float(data_lifetime_years + migration_time_years)
    urgency_gap = protection_window - years_until_quantum

    if urgency_gap > 3.0:
        mosca_score = 100.0
        mosca_status = "DEADLINE_RISK"
        rationale = (
            f"DEADLINE RISK: Protection window X+Y ({data_lifetime_years:.1f}y + {migration_time_years:.1f}y = {protection_window:.1f}y) "
            f"exceeds remaining threat horizon Z ({years_until_quantum:.1f}y) by {urgency_gap:.1f} years."
        )
    elif urgency_gap > 0.0:
        mosca_score = 80.0
        mosca_status = "MIGRATION_REQUIRED"
        rationale = (
            f"MIGRATION REQUIRED: Protection window X+Y ({protection_window:.1f}y) exceeds threat horizon Z ({years_until_quantum:.1f}y). "
            f"Migration must begin immediately."
        )
    elif urgency_gap >= -3.0:
        mosca_score = 50.0
        mosca_status = "MIGRATION_REQUIRED"
        rationale = (
            f"MIGRATION REQUIRED: Protection window ({protection_window:.1f}y) approaches threat horizon ({years_until_quantum:.1f}y). "
            f"Margin is narrow ({abs(urgency_gap):.1f}y remaining)."
        )
    else:
        mosca_score = 20.0
        mosca_status = "SAFE_MARGIN"
        rationale = (
            f"SAFE MARGIN: Protection window ({protection_window:.1f}y) completes comfortably within threat horizon Z ({years_until_quantum:.1f}y)."
        )

    return {
        "mosca_score": mosca_score,
        "mosca_status": mosca_status,
        "urgency_gap_years": urgency_gap,
        "quantum_threat_horizon": quantum_threat_horizon_year,
        "years_until_quantum": years_until_quantum,
        "data_lifetime_years": data_lifetime_years,
        "migration_time_years": migration_time_years,
        "protection_window_years": protection_window,
        "rationale": rationale
    }


def calculate_mosca_urgency(
    data_lifetime_years: float = 10.0,
    migration_time_years: Optional[float] = None,
    quantum_threat_horizon_year: Optional[int] = None,
    current_year: Optional[int] = None,
    assets: Optional[List[Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Calculate Mosca Urgency supporting both explicit (X, Y, Z) and dynamic asset repo statistics.

    Backward compatible with default calls.
    """
    if migration_time_years is None:
        if assets:
            migration_time_years = estimate_migration_time_from_assets(assets)
        else:
            migration_time_years = 3.0

    res = calculate_mosca_analysis(data_lifetime_years, migration_time_years, quantum_threat_horizon_year, current_year)
    res["urgency_level"] = "CRITICAL" if res["mosca_score"] >= 80.0 else ("HIGH" if res["mosca_score"] >= 50.0 else "LOW")
    return res
