from typing import Dict, Any
from app.models.enums import RiskLevel, QuantumSafety
from app.risk.mosca import calculate_mosca_urgency
from app.risk.scoring import get_quantum_vulnerability_score

class RiskEngine:
    def __init__(
        self,
        weight_quantum: float = 0.25,
        weight_sensitivity: float = 0.20,
        weight_criticality: float = 0.20,
        weight_mosca: float = 0.20,
        weight_exposure: float = 0.10,
        weight_complexity: float = 0.05
    ):
        self.w_quantum = weight_quantum
        self.w_sensitivity = weight_sensitivity
        self.w_criticality = weight_criticality
        self.w_mosca = weight_mosca
        self.w_exposure = weight_exposure
        self.w_complexity = weight_complexity

    def evaluate_asset_risk(
        self,
        algorithm_name: str,
        quantum_safety: QuantumSafety,
        data_sensitivity: float = 70.0,
        business_criticality: float = 80.0,
        exposure: float = 50.0,
        migration_complexity: float = 50.0,
        data_lifetime_years: float = 10.0,
        migration_time_years: float = 3.0,
        quantum_threat_horizon_year: int = 2033
    ) -> Dict[str, Any]:
        
        # 1. Quantum Vulnerability Subscore
        quantum_vulnerability_score = get_quantum_vulnerability_score(algorithm_name, quantum_safety)

        # 2. Mosca Subscore
        mosca_result = calculate_mosca_urgency(
            data_lifetime_years=data_lifetime_years,
            migration_time_years=migration_time_years,
            quantum_threat_horizon_year=quantum_threat_horizon_year
        )
        mosca_score = mosca_result["mosca_score"]

        # 3. Weighted Total Risk Score
        total_risk_score = (
            (quantum_vulnerability_score * self.w_quantum) +
            (data_sensitivity * self.w_sensitivity) +
            (business_criticality * self.w_criticality) +
            (mosca_score * self.w_mosca) +
            (exposure * self.w_exposure) +
            (migration_complexity * self.w_complexity)
        )

        total_risk_score = round(min(100.0, max(0.0, total_risk_score)), 1)

        # 4. Risk Level Categorization
        if total_risk_score >= 80.0:
            risk_level = RiskLevel.CRITICAL
        elif total_risk_score >= 60.0:
            risk_level = RiskLevel.HIGH
        elif total_risk_score >= 35.0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        explanation = (
            f"Asset '{algorithm_name}' evaluated with overall risk score {total_risk_score}/100 ({risk_level.value}). "
            f"Quantum Vulnerability: {quantum_vulnerability_score:.0f}%, {mosca_result['explanation']}"
        )

        return {
            "risk_score": total_risk_score,
            "risk_level": risk_level,
            "quantum_vulnerability_score": quantum_vulnerability_score,
            "data_sensitivity_score": data_sensitivity,
            "business_criticality_score": business_criticality,
            "mosca_factor_score": mosca_score,
            "exposure_score": exposure,
            "migration_complexity_score": migration_complexity,
            "explanation": explanation,
            "confidence_score": 0.90
        }
