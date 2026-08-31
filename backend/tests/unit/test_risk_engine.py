from app.risk.risk_engine import RiskEngine
from app.risk.mosca import calculate_mosca_urgency
from app.models.enums import QuantumSafety, RiskLevel

def test_mosca_calculation():
    # X + Y = 10 + 3 = 13 years. Threat horizon = 2033 (7 years). Protection gap = 6 years -> CRITICAL
    res = calculate_mosca_urgency(data_lifetime_years=10, migration_time_years=3, quantum_threat_horizon_year=2033)
    assert res["mosca_score"] == 100.0
    assert res["urgency_level"] == "CRITICAL"

def test_risk_engine_rsa():
    engine = RiskEngine()
    risk = engine.evaluate_asset_risk(
        algorithm_name="RSA",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        data_sensitivity=80.0,
        business_criticality=90.0,
        quantum_threat_horizon_year=2033
    )
    assert risk["risk_score"] >= 80.0
    assert risk["risk_level"] == RiskLevel.CRITICAL
