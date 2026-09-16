from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.models.enums import RiskLevel, QuantumSafety, CryptoPurpose
from app.normalization.crypto_asset_normalizer import classify_crypto_asset
from app.risk.rules import (
    classify_algorithm_vulnerability,
    determine_crypto_purpose,
    get_sensitivity_score,
    get_criticality_score,
    get_migration_complexity_score,
    get_lifetime_exposure_score
)
from app.risk.mosca import calculate_mosca_analysis
from app.risk.scoring import (
    calculate_deterministic_risk_score,
    get_risk_level_from_score,
    calculate_confidence_score
)
from app.risk.scenarios import evaluate_threat_scenarios

from app.engines.x_engine import XEngine
from app.engines.y_engine import YEngine

class RiskEngine:
    """
    Deterministic Quantum Risk Engine for Prompt 3.
    """
    def evaluate_asset_risk(
        self,
        algorithm_name: str,
        quantum_safety: Optional[QuantumSafety] = None,
        purpose: Optional[CryptoPurpose] = None,
        asset_type: str = "ALGORITHM",
        detector_names: Optional[List[str]] = None,
        data_sensitivity_label: str = "UNKNOWN",
        business_criticality_label: str = "UNKNOWN",
        data_sensitivity: Optional[float] = None,
        business_criticality: Optional[float] = None,
        data_lifetime_years: Optional[float] = None,
        migration_time_years: Optional[float] = None,
        quantum_threat_horizon_year: Optional[int] = None,
        user_x_years: Optional[float] = None,
        user_domain: Optional[str] = None,
        user_y_scenario: Optional[str] = None,
        evidence_excerpts: Optional[List[str]] = None
    ) -> Dict[str, Any]:

        # 0. Artefact Classification
        classification = classify_crypto_asset(algorithm_name, asset_type=asset_type, purpose=purpose)
        if business_criticality_label == "UNKNOWN":
            business_criticality_label = classification["business_criticality_label"]
        if data_lifetime_years is None and classification.get("data_lifetime_years") != 10.0:
            data_lifetime_years = classification.get("data_lifetime_years")

        # 1. Quantum Vulnerability Classification
        classified_qs, quantum_exposure, qs_rationale = classify_algorithm_vulnerability(algorithm_name)

        # Use classified_qs unless explicit quantum_safety was provided and is not UNKNOWN
        final_qs = quantum_safety if (quantum_safety and quantum_safety != QuantumSafety.UNKNOWN) else classified_qs
        if final_qs != classified_qs:
            # Re-evaluate score if explicit safety overrides default classification
            if final_qs == QuantumSafety.QUANTUM_VULNERABLE:
                quantum_exposure = 100.0
            elif final_qs == QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN:
                quantum_exposure = 30.0
            elif final_qs in [QuantumSafety.QUANTUM_SAFE, QuantumSafety.NOT_DIRECTLY_QUANTUM_VULNERABLE]:
                quantum_exposure = 10.0
            else:
                quantum_exposure = 50.0

        # 2. Purpose Mapping
        final_purpose = determine_crypto_purpose(algorithm_name, purpose)

        # 3. Sensitivity & Criticality Scores
        sensitivity_score = data_sensitivity if data_sensitivity is not None else get_sensitivity_score(data_sensitivity_label)
        criticality_score = business_criticality if business_criticality is not None else get_criticality_score(business_criticality_label)

        # 4. Migration Complexity
        complexity_score, complexity_rationale = get_migration_complexity_score(asset_type, detector_names or [])

        # 5. Canonical Mosca Evaluation & Single Z Consistency
        comp_dict = {
            "primitive": algorithm_name,
            "algorithm_name": algorithm_name,
            "purpose": final_purpose.value if hasattr(final_purpose, "value") else str(final_purpose),
            "asset_type": asset_type
        }
        from app.engines.mosca_engine import MoscaEngine
        m_eval = MoscaEngine().evaluate_component_mosca(
            component=comp_dict,
            user_x_years=user_x_years if user_x_years is not None else data_lifetime_years,
            user_domain=user_domain,
            user_y_scenario=user_y_scenario
        )

        effective_x = float(m_eval["x"]["value"])
        effective_y = float(migration_time_years) if migration_time_years is not None else float(m_eval["y"]["value"])
        z_target = m_eval["z"].get("z_target_year")
        resolved_z_year = int(quantum_threat_horizon_year) if quantum_threat_horizon_year is not None else (int(z_target) if z_target is not None else 2033)

        lifetime_score, lifetime_rationale = get_lifetime_exposure_score(
            data_lifetime_years=effective_x,
            migration_time_years=effective_y,
            quantum_threat_horizon_year=resolved_z_year
        )

        mosca = calculate_mosca_analysis(
            data_lifetime_years=effective_x,
            migration_time_years=effective_y,
            quantum_threat_horizon_year=resolved_z_year
        )
        mosca["quantum_threat_horizon"] = resolved_z_year
        mosca["x_years"] = effective_x
        mosca["y_years"] = effective_y
        mosca["z_horizon_years"] = m_eval["z"].get("z_planning_horizon_years")
        mosca["z_score"] = m_eval["z"].get("z_score")
        mosca["mosca_score"] = m_eval.get("mosca_score", mosca.get("mosca_score", 50.0))
        mosca["technical_urgency"] = m_eval.get("technical_urgency", "MODERATE")
        mosca["x_source"] = m_eval["x"].get("source", "default")
        mosca["y_scenario"] = m_eval["y"].get("scenario", "STANDARD")

        # 6. Overall Deterministic Risk Score
        risk_score = calculate_deterministic_risk_score(
            quantum_exposure=quantum_exposure,
            data_sensitivity=sensitivity_score,
            business_criticality=criticality_score,
            migration_complexity=complexity_score,
            lifetime_exposure=lifetime_score
        )

        # 7. Risk Level Thresholds
        risk_level = get_risk_level_from_score(risk_score)

        # Urgency / Priority Classification
        if risk_score >= 75.0 or mosca["mosca_status"] == "DEADLINE_RISK":
            priority = "CRITICAL"
        elif risk_score >= 50.0 or mosca["mosca_status"] == "MIGRATION_REQUIRED":
            priority = "HIGH"
        elif risk_score >= 25.0:
            priority = "MODERATE"
        else:
            priority = "LOW"

        # 8. Confidence Score (Independent of Risk Score)
        confidence_score = calculate_confidence_score(detector_names or [], len(evidence_excerpts or []))

        # 9. Threat Scenarios
        scenarios = evaluate_threat_scenarios(
            algorithm_name=algorithm_name,
            quantum_safety=final_qs,
            purpose=final_purpose,
            data_sensitivity_label=data_sensitivity_label,
            data_lifetime_years=effective_x,
            mosca_status=mosca["mosca_status"],
            evidence_excerpts=evidence_excerpts
        )

        # 10. Evidence-Driven Rationale
        rationale_items = [
            qs_rationale,
            f"Asset purpose is classified as '{final_purpose.value if hasattr(final_purpose, 'value') else final_purpose}'.",
            f"Data sensitivity is '{data_sensitivity_label.upper()}' ({sensitivity_score:.0f}/100) and business criticality is '{business_criticality_label.upper()}' ({criticality_score:.0f}/100).",
            complexity_rationale,
            mosca["rationale"],
            f"Confidence score is {confidence_score:.2f} based on evidence detection methods."
        ]

        factors = {
            "quantum_exposure": quantum_exposure,
            "data_sensitivity": sensitivity_score,
            "business_criticality": criticality_score,
            "migration_complexity": complexity_score,
            "lifetime_exposure": lifetime_score,
            "mosca_score": mosca["mosca_score"],
            "x_years": effective_x,
            "y_years": effective_y,
            "z_score": m_eval["z"].get("z_score")
        }

        return {
            "algorithm_name": algorithm_name,
            "quantum_status": final_qs.value if hasattr(final_qs, "value") else str(final_qs),
            "crypto_purpose": final_purpose.value if hasattr(final_purpose, "value") else str(final_purpose),
            "classification": classification,
            "risk_score": risk_score,
            "risk_level": risk_level.value if hasattr(risk_level, "value") else str(risk_level),
            "priority": priority,
            "confidence_score": confidence_score,
            "x": m_eval["x"],
            "y": m_eval["y"],
            "z": m_eval["z"],
            "factors": factors,
            "mosca": mosca,
            "threat_scenarios": scenarios,
            "rationale": rationale_items,
            "explanation": " ".join(rationale_items)
        }
