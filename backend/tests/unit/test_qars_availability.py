import pytest
from app.qars.availability import evaluate_availability
from app.qars.models import QARSAvailability, QARSValidationError
from app.qars.service import evaluate_artifact_qars


def test_1_rating_1_to_zero_score():
    res = evaluate_availability(asset={}, availability_impact_override=1.0)
    assert res.score == 0.0
    assert res.raw_rating == 1.0


def test_2_rating_5_to_one_score():
    res = evaluate_availability(asset={}, availability_impact_override=5.0)
    assert res.score == 1.0
    assert res.raw_rating == 5.0


def test_3_rating_3_to_half_score():
    res = evaluate_availability(asset={}, availability_impact_override=3.0)
    assert res.score == 0.5
    assert res.raw_rating == 3.0


def test_4_invalid_rating_raises_validation_error():
    with pytest.raises(QARSValidationError, match="Invalid availabilityImpact rating"):
        evaluate_availability(asset={}, availability_impact_override=6.0)

    with pytest.raises(QARSValidationError, match="Invalid availabilityImpact rating"):
        evaluate_availability(asset={}, availability_impact_override=0.0)


def test_5_user_override_provenance():
    proj = {"business_context": {"factor_ratings": {"availabilityImpact": 5}}}
    res = evaluate_availability(asset={}, project=proj)
    assert res.provenance == "USER_OVERRIDE"
    assert res.score == 1.0


def test_6_application_default_provenance():
    proj = {"business_context": {}}
    res = evaluate_availability(asset={}, project=proj)
    assert res.provenance == "APPLICATION_DEFAULT"
    assert res.raw_rating == 4.0
    assert res.score == 0.75


def test_7_missing_rating_fallback():
    res = evaluate_availability(asset={})
    assert res.provenance == "APPLICATION_DEFAULT"
    assert res.raw_rating == 4.0
    assert res.score == 0.75


def test_8_no_label_to_number_conversion():
    # Proof that rating number 2.0 produces score 0.25 rather than looking at label "HIGH" or "MEDIUM"
    proj = {"business_context": {"factor_ratings": {"availabilityImpact": 2}}}
    res = evaluate_availability(asset={}, project=proj)
    assert res.score == 0.25
    assert res.raw_rating == 2.0


def test_9_secondary_blast_radius_evidence_preserved():
    asset = {
        "extra_metadata": {
            "blast_radius_score": 65.5,
            "affected_nodes_count": 8
        }
    }
    res = evaluate_availability(asset=asset, availability_impact_override=4.0)
    assert res.evidence.get("blast_radius_score") == 65.5
    assert res.evidence.get("affected_nodes_count") == 8


def test_10_missing_av_fields_reported():
    res = evaluate_availability(asset={})
    assert "downtime_financial_cost_per_hour" in res.missing_factors
    assert "sla_availability_target_percentage" in res.missing_factors
    assert "active_user_operations_impact_count" in res.missing_factors
    assert "external_service_topology" in res.missing_factors


def test_26_real_av_result_attached_to_service_output():
    asset = {
        "id": "asset-123",
        "algorithm": "RSA-2048",
        "extra_metadata": {
            "x_years": 5.0,
            "data_sensitivity": 4.0,
            "exposure": 3.0,
        }
    }
    res = evaluate_artifact_qars(asset=asset)
    assert res.availability is not None
    assert isinstance(res.availability, QARSAvailability)
    assert res.availability.score == 0.75


def test_28_final_score_remains_equal_to_core_score():
    asset = {
        "id": "asset-123",
        "algorithm": "RSA-2048",
        "extra_metadata": {
            "x_years": 5.0,
            "data_sensitivity": 4.0,
            "exposure": 3.0,
        }
    }
    res = evaluate_artifact_qars(asset=asset)
    assert res.final_score >= res.base_score
    assert res.final_score <= 100.0



def test_29_existing_xyzse_behavior_unchanged():
    class TestAsset:
        def __init__(self):
            self.id = "asset-123"
            self.algorithm = "RSA-2048"
            self.algorithm_name = "RSA-2048"
            self.asset_type = "ALGORITHM"
            self.purpose = "ENCRYPTION"
            self.extra_metadata = {
                "context_overrides": {
                    "x_years": 10.0,
                },
                "data_sensitivity": 5.0,
                "exposure": 4.0,
            }
    asset = TestAsset()
    res = evaluate_artifact_qars(asset=asset)
    assert res.core_input.x_years == 10.0
    assert res.core_input.data_sensitivity == 5.0
    assert res.core_input.exposure == 4.0


def test_30_existing_aqr_behavior_unchanged():
    asset = {
        "id": "asset-123",
        "algorithm": "RSA-2048",
        "extra_metadata": {
            "x_years": 5.0,
            "data_sensitivity": 4.0,
            "exposure": 3.0,
        }
    }
    res = evaluate_artifact_qars(asset=asset)
    assert res.algorithm_risk is not None
    assert res.algorithm_risk.canonical_algorithm == "RSA"
    assert res.algorithm_risk.aqr_score == pytest.approx(0.72)
