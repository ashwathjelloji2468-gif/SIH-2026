from datetime import datetime, timezone

def calculate_mosca_urgency(
    data_lifetime_years: float,     # X
    migration_time_years: float,    # Y
    quantum_threat_horizon_year: int # Z
) -> dict:
    """
    Mosca's Theorem: If X + Y > Z, data security is compromised before migration completes.
    - X: Required data protection lifetime (years)
    - Y: Time required to migrate infrastructure (years)
    - Z: Time until a quantum computer capable of breaking current cryptography exists (threat horizon)
    """
    current_year = datetime.now(timezone.utc).year
    years_until_quantum = max(1, quantum_threat_horizon_year - current_year)

    protection_window = data_lifetime_years + migration_time_years
    urgency_gap = protection_window - years_until_quantum

    if urgency_gap > 5:
        mosca_score = 100.0
        urgency_level = "CRITICAL"
        explanation = f"Mosca Violation: X ({data_lifetime_years}y) + Y ({migration_time_years}y) = {protection_window}y exceeds threat horizon ({years_until_quantum}y remaining) by {urgency_gap:.1f} years."
    elif urgency_gap > 0:
        mosca_score = 75.0 + (urgency_gap / 5.0) * 20.0
        urgency_level = "HIGH"
        explanation = f"Mosca Warning: Protection lifetime ({protection_window}y) exceeds threat horizon ({years_until_quantum}y remaining)."
    else:
        mosca_score = max(10.0, 50.0 + (urgency_gap / 10.0) * 40.0)
        urgency_level = "MEDIUM" if mosca_score > 30 else "LOW"
        explanation = f"Mosca Safe: Protection window ({protection_window}y) completes within threat horizon ({years_until_quantum}y remaining)."

    return {
        "mosca_score": min(100.0, max(0.0, mosca_score)),
        "urgency_level": urgency_level,
        "urgency_gap_years": urgency_gap,
        "explanation": explanation,
        "x_lifetime": data_lifetime_years,
        "y_migration": migration_time_years,
        "z_horizon": quantum_threat_horizon_year
    }
