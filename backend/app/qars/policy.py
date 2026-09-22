from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Any
from app.qars.config import QARSConfig, DEFAULT_QARS_CONFIG
from app.qars.models import (
    QARSCoreOutput,
    QARSPolicyInput,
    QARSExplanation,
    QARSResult,
    QARSAlgorithmRisk,
    SecurityObjectiveResult,
    QARSAvailability,
    QARSCryptoAgilityEvidence,
)
from app.qars.policy_calibration import load_policy_calibration


class ComponentProvider(ABC):
    """
    Abstract Provider Boundary for component evaluation.
    Allows future code to supply component values/adjustments via rule engines
    or ML frameworks without modifying QARS Core or Policy Engine structure.
    """
    @abstractmethod
    def evaluate_adjustments(self, policy_input: QARSPolicyInput) -> Dict[str, float]:
        """
        Evaluates and returns bounded component adjustments as a dictionary.
        """
        pass


class RuleComponentProvider(ComponentProvider):
    """
    Default Rule-Based Component Provider for Phase 4.
    Evaluates bounded, calibrated component adjustments from qars_policy_calibration.json.
    Unconfigured components return 0.0 adjustment without lowering risk.
    """
    def evaluate_adjustments(self, policy_input: QARSPolicyInput) -> Dict[str, float]:
        adjustments: Dict[str, float] = {}
        calib = load_policy_calibration()
        max_adj = calib.get("max_adjustments", {})
        total_bound = float(calib.get("total_max_adjustment_bound", 25.0))

        # 1. Algorithm Risk (AQR)
        if policy_input.algorithm_risk is not None:
            if isinstance(policy_input.algorithm_risk, QARSAlgorithmRisk) and policy_input.algorithm_risk.aqr_score is not None:
                max_b = float(max_adj.get("algorithm_risk", 15.0))
                adj_val = min(max_b, round(float(policy_input.algorithm_risk.aqr_score) * 10.0, 2))
                adjustments["algorithm_risk"] = adj_val
            else:
                adjustments["algorithm_risk"] = 0.0

        # 2. Availability (AV)
        if policy_input.availability is not None:
            if isinstance(policy_input.availability, QARSAvailability) and policy_input.availability.score is not None:
                max_b = float(max_adj.get("availability", 10.0))
                adj_val = min(max_b, round(float(policy_input.availability.score) * 5.0, 2))
                adjustments["availability"] = adj_val
            else:
                adjustments["availability"] = 0.0

        # 3. Crypto Agility (CAR)
        if policy_input.crypto_agility is not None:
            if isinstance(policy_input.crypto_agility, QARSCryptoAgilityEvidence) and policy_input.crypto_agility.car_score is not None:
                max_b = float(max_adj.get("crypto_agility", 15.0))
                adj_val = min(max_b, round((float(policy_input.crypto_agility.car_score) / 100.0) * 10.0, 2))
                adjustments["crypto_agility"] = adj_val
            else:
                adjustments["crypto_agility"] = 0.0

        # 4. Migration Complexity (MC)
        if policy_input.migration_complexity is not None:
            mc_obj = policy_input.migration_complexity
            mc_score = getattr(mc_obj, "score", None) if hasattr(mc_obj, "score") else (float(mc_obj) if isinstance(mc_obj, (int, float)) else None)
            if mc_score is not None:
                max_b = float(max_adj.get("migration_complexity", 15.0))
                adj_val = min(max_b, round((float(mc_score) / 100.0) * 10.0, 2))
                adjustments["migration_complexity"] = adj_val
            else:
                adjustments["migration_complexity"] = 0.0

        # Clamp total adjustments to total_bound
        total_sum = sum(adjustments.values())
        if total_sum > total_bound and total_sum > 0:
            scale = total_bound / total_sum
            adjustments = {k: round(v * scale, 2) for k, v in adjustments.items()}

        return adjustments


class MLComponentProvider(ComponentProvider):
    """
    Stub for future Machine Learning Component Provider.
    Demonstrates architectural swappability without requiring ML dependencies or fake predictions.
    """
    def evaluate_adjustments(self, policy_input: QARSPolicyInput) -> Dict[str, float]:
        return {}


class QARSPolicyEngine:
    """
    Configurable Policy & Rule Engine for QARS.
    Applies bounded rule adjustments to QARS Core base score and resolves final severity level.
    """
    def __init__(
        self,
        config: Optional[QARSConfig] = None,
        provider: Optional[ComponentProvider] = None,
    ):
        self.config = config or DEFAULT_QARS_CONFIG
        self.provider = provider or RuleComponentProvider()

    def evaluate(
        self,
        core_output: QARSCoreOutput,
        policy_input: Optional[QARSPolicyInput] = None,
    ) -> QARSResult:
        if policy_input is None:
            policy_input = QARSPolicyInput()

        # Base score comes directly from QARS Core
        base_score = core_output.score

        # Get component adjustments from current provider
        adjustments = self.provider.evaluate_adjustments(policy_input)

        # Total adjustment sum
        total_adjustment = sum(adjustments.values())

        # Final score clamped 0..100
        final_score = min(100.0, max(0.0, base_score + total_adjustment))

        # Severity level resolved via centralized configuration
        level = self.config.resolve_level(final_score)

        # Reconstruct unnormalized S and E for explanation
        s_used = (
            policy_input.core_input.data_sensitivity
            if policy_input.core_input
            else (core_output.sensitivity_normalized * 4.0 + 1.0)
        )
        e_used = (
            policy_input.core_input.exposure
            if policy_input.core_input
            else (core_output.exposure_normalized * 4.0 + 1.0)
        )

        alg_risk: Optional[QARSAlgorithmRisk] = None
        sec_objs: Optional[List[str]] = None
        avail_res: Optional[QARSAvailability] = None
        agility_res: Optional[QARSCryptoAgilityEvidence] = None
        mc_res: Optional[Any] = None
        z_uncert: Optional[Any] = None

        if isinstance(policy_input.algorithm_risk, QARSAlgorithmRisk):
            alg_risk = policy_input.algorithm_risk
            sec_objs = alg_risk.security_objectives

        if sec_objs is None and policy_input.security_objectives is not None:
            if isinstance(policy_input.security_objectives, SecurityObjectiveResult):
                sec_objs = policy_input.security_objectives.objectives
            elif isinstance(policy_input.security_objectives, list):
                sec_objs = policy_input.security_objectives

        if isinstance(policy_input.availability, QARSAvailability):
            avail_res = policy_input.availability

        if isinstance(policy_input.crypto_agility, QARSCryptoAgilityEvidence):
            agility_res = policy_input.crypto_agility

        if policy_input.migration_complexity is not None:
            mc_res = policy_input.migration_complexity

        if policy_input.z_uncertainty is not None:
            z_uncert = policy_input.z_uncertainty

        # Structured explanation
        explanation = QARSExplanation(
            x_years=core_output.x_years,
            y_years=core_output.y_years,
            z_years=core_output.z_years,
            data_sensitivity=s_used,
            exposure=e_used,
            sensitivity_normalized=core_output.sensitivity_normalized,
            exposure_normalized=core_output.exposure_normalized,
            timeline_pressure=core_output.timeline_pressure,
            core_score=base_score,
            active_adjustments=adjustments,
            final_score=final_score,
            severity_level=level.value,
            algorithm_risk=alg_risk,
            security_objectives=sec_objs,
            availability=avail_res,
            crypto_agility_evidence=agility_res,
            migration_complexity=mc_res,
            z_uncertainty=z_uncert,
        )

        return QARSResult(
            base_score=base_score,
            adjustments=adjustments,
            final_score=final_score,
            level=level,
            explanation=explanation,
            algorithm_risk=alg_risk,
            availability=avail_res,
            crypto_agility_evidence=agility_res,
            migration_complexity=mc_res,
            z_uncertainty=z_uncert,
        )
