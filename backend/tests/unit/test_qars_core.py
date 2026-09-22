import pytest
from app.qars.models import QARSCoreInput, QARSValidationError
from app.qars.core import compute_qars_core


def test_qars_core_normal_calculation():
    # S=3 -> Sn=(3-1)/4 = 0.5
    # E=3 -> En=(3-1)/4 = 0.5
    # X=5, Y=5, Z=5 -> T = (5+5-5)/5 = 1.0
    # QARS_core = 100 * 1.0 * 0.5 * 0.5 = 25.0
    inp = QARSCoreInput(
        x_years=5.0,
        y_years=5.0,
        z_years=5.0,
        data_sensitivity=3.0,
        exposure=3.0
    )
    res = compute_qars_core(inp)
    assert res.score == 25.0
    assert res.timeline_pressure == 1.0
    assert res.sensitivity_normalized == 0.5
    assert res.exposure_normalized == 0.5


def test_qars_core_timeline_pressure_below_zero():
    # X=2, Y=1, Z=5 -> (2+1-5)/5 = -0.4 -> clamped T = 0.0
    inp = QARSCoreInput(
        x_years=2.0,
        y_years=1.0,
        z_years=5.0,
        data_sensitivity=5.0,
        exposure=5.0
    )
    res = compute_qars_core(inp)
    assert res.timeline_pressure == 0.0
    assert res.score == 0.0


def test_qars_core_timeline_pressure_above_one():
    # X=10, Y=10, Z=5 -> (10+10-5)/5 = 3.0 -> clamped T = 1.0
    inp = QARSCoreInput(
        x_years=10.0,
        y_years=10.0,
        z_years=5.0,
        data_sensitivity=5.0,
        exposure=5.0
    )
    res = compute_qars_core(inp)
    assert res.timeline_pressure == 1.0
    assert res.score == 100.0


def test_qars_core_minimum_sensitivity():
    # S=1 -> Sn=0.0 -> score = 0.0
    inp = QARSCoreInput(
        x_years=5.0,
        y_years=5.0,
        z_years=5.0,
        data_sensitivity=1.0,
        exposure=5.0
    )
    res = compute_qars_core(inp)
    assert res.sensitivity_normalized == 0.0
    assert res.score == 0.0


def test_qars_core_maximum_sensitivity():
    # S=5 -> Sn=1.0
    inp = QARSCoreInput(
        x_years=5.0,
        y_years=5.0,
        z_years=5.0,
        data_sensitivity=5.0,
        exposure=5.0
    )
    res = compute_qars_core(inp)
    assert res.sensitivity_normalized == 1.0
    assert res.score == 100.0


def test_qars_core_minimum_exposure():
    # E=1 -> En=0.0 -> score = 0.0
    inp = QARSCoreInput(
        x_years=5.0,
        y_years=5.0,
        z_years=5.0,
        data_sensitivity=5.0,
        exposure=1.0
    )
    res = compute_qars_core(inp)
    assert res.exposure_normalized == 0.0
    assert res.score == 0.0


def test_qars_core_maximum_exposure():
    # E=5 -> En=1.0
    inp = QARSCoreInput(
        x_years=5.0,
        y_years=5.0,
        z_years=5.0,
        data_sensitivity=5.0,
        exposure=5.0
    )
    res = compute_qars_core(inp)
    assert res.exposure_normalized == 1.0
    assert res.score == 100.0


def test_qars_core_invalid_sensitivity():
    with pytest.raises(QARSValidationError):
        compute_qars_core(QARSCoreInput(x_years=5, y_years=0, z_years=5, data_sensitivity=0.5, exposure=3.0))

    with pytest.raises(QARSValidationError):
        compute_qars_core(QARSCoreInput(x_years=5, y_years=0, z_years=5, data_sensitivity=5.5, exposure=3.0))


def test_qars_core_invalid_exposure():
    with pytest.raises(QARSValidationError):
        compute_qars_core(QARSCoreInput(x_years=5, y_years=0, z_years=5, data_sensitivity=3.0, exposure=0.0))

    with pytest.raises(QARSValidationError):
        compute_qars_core(QARSCoreInput(x_years=5, y_years=0, z_years=5, data_sensitivity=3.0, exposure=6.0))


def test_qars_core_invalid_z():
    with pytest.raises(QARSValidationError):
        compute_qars_core(QARSCoreInput(x_years=5, y_years=0, z_years=0, data_sensitivity=3.0, exposure=3.0))

    with pytest.raises(QARSValidationError):
        compute_qars_core(QARSCoreInput(x_years=5, y_years=0, z_years=-1, data_sensitivity=3.0, exposure=3.0))


def test_qars_core_invalid_x():
    with pytest.raises(QARSValidationError):
        compute_qars_core(QARSCoreInput(x_years=0, y_years=0, z_years=5, data_sensitivity=3.0, exposure=3.0))

    with pytest.raises(QARSValidationError):
        compute_qars_core(QARSCoreInput(x_years=-2, y_years=0, z_years=5, data_sensitivity=3.0, exposure=3.0))


def test_qars_core_invalid_y():
    with pytest.raises(QARSValidationError):
        compute_qars_core(QARSCoreInput(x_years=5, y_years=-1, z_years=5, data_sensitivity=3.0, exposure=3.0))


def test_qars_core_bounded_score():
    # Extremely large inputs must clamp core score to [0, 100]
    inp = QARSCoreInput(
        x_years=1000.0,
        y_years=500.0,
        z_years=1.0,
        data_sensitivity=5.0,
        exposure=5.0
    )
    res = compute_qars_core(inp)
    assert 0.0 <= res.score <= 100.0
    assert res.score == 100.0
