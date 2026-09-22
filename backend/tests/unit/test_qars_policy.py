import pytest
from app.qars.config import QARSConfig, QARSLevel
from app.qars.models import (
    QARSCoreInput,
    QARSPolicyInput,
    QARSAlgorithmRisk,
    QARSAvailability,
    QARSCryptoAgilityEvidence,
)
from app.qars.core import compute_qars_core, calculate_qars
from app.qars.policy import (
    QARSPolicyEngine,
    RuleComponentProvider,
    MLComponentProvider,
    ComponentProvider,
)
from app.qars.migration import QARSMigrationComplexity


def test_qars_policy_phase1_final_score_equals_core_score():
    inp = QARSCoreInput(
        x_years=5.0,
        y_years=5.0,
        z_years=5.0,
        data_sensitivity=3.0,
        exposure=3.0,
    )
    res = calculate_qars(inp)
    assert res.base_score == 25.0
    assert res.final_score == 25.0
    assert res.final_score == res.base_score


def test_qars_policy_no_future_component_fabricated():
    inp = QARSCoreInput(
        x_years=5.0,
        y_years=5.0,
        z_years=5.0,
        data_sensitivity=4.0,
        exposure=4.0,
    )
    pol_input = QARSPolicyInput(
        core_input=inp,
        algorithm_risk=None,
        availability=None,
        crypto_agility=None,
        migration_complexity=None,
    )
    res = calculate_qars(inp, policy_input=pol_input)
    for val in res.adjustments.values():
        assert val == 0.0
    assert sum(res.adjustments.values()) == 0.0


def test_qars_policy_phase4_bounded_adjustments():
    inp = QARSCoreInput(x_years=5, y_years=5, z_years=5, data_sensitivity=3, exposure=3)
    alg_risk = QARSAlgorithmRisk(
        algorithm="RSA-2048",
        canonical_algorithm="RSA-2048",
        attack_family="SHOR",
        aqr_score=0.8,
        calibration_status="CONFIGURED",
        confidence="HIGH",
        quantum_attack="SHOR",
        explanation="Shor"
    )
    mc = QARSMigrationComplexity(
        score=50.0,
        status="CONFIGURED"
    )
    pol_input = QARSPolicyInput(
        core_input=inp,
        algorithm_risk=alg_risk,
        migration_complexity=mc
    )
    res = calculate_qars(inp, policy_input=pol_input)
    assert res.base_score == 25.0
    assert "algorithm_risk" in res.adjustments
    assert "migration_complexity" in res.adjustments
    assert res.adjustments["algorithm_risk"] > 0.0
    assert res.adjustments["migration_complexity"] > 0.0
    assert res.final_score > res.base_score
    assert res.final_score <= 100.0


def test_qars_policy_unconfigured_components_do_not_lower_risk():
    inp = QARSCoreInput(x_years=5, y_years=5, z_years=5, data_sensitivity=3, exposure=3)
    pol_input = QARSPolicyInput(
        core_input=inp,
        algorithm_risk=None,
        availability=None,
        crypto_agility=None,
        migration_complexity=None
    )
    res = calculate_qars(inp, policy_input=pol_input)
    assert res.final_score >= res.base_score


def test_qars_policy_severity_thresholds_from_config():
    custom_config = QARSConfig(
        low_max=10.0,
        medium_max=30.0,
        high_max=60.0,
        critical_max=100.0,
    )

    inp_low = QARSCoreInput(x_years=1, y_years=0, z_years=5, data_sensitivity=2.0, exposure=2.0)
    res_low = calculate_qars(inp_low, config=custom_config)
    assert res_low.level == QARSLevel.LOW

    inp_med = QARSCoreInput(x_years=5, y_years=5, z_years=5, data_sensitivity=3.0, exposure=3.0)
    res_med = calculate_qars(inp_med, config=custom_config)
    assert res_med.base_score == 25.0
    assert res_med.level == QARSLevel.MEDIUM


def test_qars_policy_explanation_contains_active_calculations():
    inp = QARSCoreInput(
        x_years=4.0,
        y_years=2.0,
        z_years=3.0,
        data_sensitivity=4.0,
        exposure=5.0,
    )
    res = calculate_qars(inp)
    exp = res.explanation

    assert exp.x_years == 4.0
    assert exp.y_years == 2.0
    assert exp.z_years == 3.0
    assert exp.data_sensitivity == 4.0
    assert exp.exposure == 5.0
    assert exp.sensitivity_normalized == (4.0 - 1.0) / 4.0
    assert exp.exposure_normalized == (5.0 - 1.0) / 4.0
    assert exp.timeline_pressure == 1.0
    assert exp.core_score == res.base_score
    assert exp.final_score == res.final_score
    assert exp.severity_level == res.level.value
    assert isinstance(exp.active_adjustments, dict)


def test_qars_policy_provider_boundary_swappability():
    class TestCustomProvider(ComponentProvider):
        def evaluate_adjustments(self, policy_input: QARSPolicyInput) -> dict:
            return {"custom_rule": 5.0}

    inp = QARSCoreInput(
        x_years=5.0,
        y_years=5.0,
        z_years=5.0,
        data_sensitivity=3.0,
        exposure=3.0,
    )
    res = calculate_qars(inp, provider=TestCustomProvider())
    assert res.base_score == 25.0
    assert res.adjustments == {"custom_rule": 5.0}
    assert res.final_score == 30.0

    res_ml = calculate_qars(inp, provider=MLComponentProvider())
    assert res_ml.base_score == 25.0
    assert res_ml.final_score == 25.0
