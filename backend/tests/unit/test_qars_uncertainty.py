import pytest
from app.qars.uncertainty import evaluate_z_uncertainty, QARSZUncertainty


def test_z_uncertainty_central_preservation():
    z_res = {
        "z_value": 8.5,
        "confidence": "HIGH"
    }
    res = evaluate_z_uncertainty(z_res)
    assert isinstance(res, QARSZUncertainty)
    assert res.z_central == 8.5
    assert res.z_low is None
    assert res.z_high is None
    assert res.status == "POINT_ESTIMATE_ONLY"
    assert res.source == "Z_ENGINE"
    assert res.confidence == "HIGH"
    assert "statistical lower/upper timeline bounds are not currently available" in res.explanation.lower()


def test_z_uncertainty_categorical_confidence_preserved():
    z_res = {
        "value_years_remaining": 5.0,
        "confidence": "MEDIUM"
    }
    res = evaluate_z_uncertainty(z_res)
    assert res.z_central == 5.0
    assert res.confidence == "MEDIUM"
