import pytest
from types import SimpleNamespace
from app.qars.config import QARSConfig, QARSLevel
from app.qars.models import QARSValidationError
from app.qars.service import evaluate_artifact_qars


def create_mock_asset(
    asset_id="asset-101",
    algorithm_name="RSA-2048",
    project_id="proj-999",
    scan_id="scan-888",
    extra_metadata=None,
    location="crypto/rsa_key.py",
):
    return SimpleNamespace(
        id=asset_id,
        algorithm_name=algorithm_name,
        project_id=project_id,
        scan_id=scan_id,
        location=location,
        purpose="ENCRYPTION",
        asset_type="ALGORITHM",
        key_size=2048,
        extra_metadata=extra_metadata or {},
    )


def create_mock_project(
    project_id="proj-999",
    user_x_years=5,
    user_y_scenario="STANDARD",
    business_context=None,
):
    if business_context is None:
        business_context = {"factor_ratings": {"dataSensitivity": 4, "exposureRating": 4}}
    return SimpleNamespace(
        id=project_id,
        name="Mock Project",
        description="Test project",
        repository_url="https://github.com/org/repo",
        user_x_years=user_x_years,
        user_domain="FINTECH",
        user_y_scenario=user_y_scenario,
        business_context=business_context,
    )


def test_qars_service_x_from_effective_context():
    # Test X resolved from project user_x_years via XEngine -> USER_OVERRIDE
    asset = create_mock_asset()
    project = create_mock_project(user_x_years=7)
    res = evaluate_artifact_qars(asset, project)

    assert res.core_input.x_years == 7.0
    assert res.provenance.x_source == "USER_OVERRIDE"


def test_qars_service_s_from_effective_context():
    # Test S resolved from project business context factor_ratings
    asset = create_mock_asset()
    project = create_mock_project(business_context={"factor_ratings": {"dataSensitivity": 5, "exposureRating": 4}})
    res = evaluate_artifact_qars(asset, project)

    assert res.core_input.data_sensitivity == 5.0
    assert res.provenance.s_source == "APPLICATION_DEFAULT"


def test_qars_service_numeric_artifact_exposure_override():
    # Test numeric artifact exposure override
    asset_with_override = create_mock_asset(
        extra_metadata={"context_overrides": {"exposure_rating": 2.0}}
    )
    project = create_mock_project(business_context={"factor_ratings": {"exposureRating": 5}})
    res = evaluate_artifact_qars(asset_with_override, project)

    assert res.core_input.exposure == 2.0
    assert res.provenance.e_source == "ARTIFACT_EVIDENCE"


def test_qars_service_numeric_project_exposure_rating():
    # Test numeric project factor_ratings exposureRating
    asset = create_mock_asset()
    project = create_mock_project(business_context={"factor_ratings": {"exposureRating": 3}})
    res = evaluate_artifact_qars(asset, project)

    assert res.core_input.exposure == 3.0
    assert res.provenance.e_source == "USER_OVERRIDE"


def test_qars_service_artifact_exposure_takes_precedence():
    # Test artifact exposure override takes precedence over project setting
    asset_with_override = create_mock_asset(
        extra_metadata={"context_overrides": {"exposure_rating": 1.0}}
    )
    project = create_mock_project(business_context={"factor_ratings": {"exposureRating": 5}})
    res = evaluate_artifact_qars(asset_with_override, project)

    assert res.core_input.exposure == 1.0
    assert res.provenance.e_source == "ARTIFACT_EVIDENCE"


def test_qars_service_string_external_facing_does_not_produce_e4(monkeypatch):
    # Verify EXTERNAL_FACING string alone without numeric rating source fails and does NOT produce E=4
    import app.services.business_criticality_service as bcs
    monkeypatch.setattr(bcs, "DEFAULT_RATINGS", {})
    asset = create_mock_asset()
    project = create_mock_project(business_context={})

    with pytest.raises(QARSValidationError) as excinfo:
        evaluate_artifact_qars(asset, project)
    assert "exposure" in str(excinfo.value)


def test_qars_service_string_internal_does_not_produce_e2(monkeypatch):
    # Verify INTERNAL string alone without numeric rating source fails and does NOT produce E=2
    import app.services.business_criticality_service as bcs
    monkeypatch.setattr(bcs, "DEFAULT_RATINGS", {})
    asset = create_mock_asset()
    project = create_mock_project(business_context={})

    with pytest.raises(QARSValidationError) as excinfo:
        evaluate_artifact_qars(asset, project)
    assert "exposure" in str(excinfo.value)


def test_qars_service_y_from_yengine():
    # Test Y resolved from YEngine using user_y_scenario
    asset = create_mock_asset()
    project = create_mock_project(user_y_scenario="FAST")  # FAST = 5 years
    res = evaluate_artifact_qars(asset, project)

    assert res.core_input.y_years == 5.0
    assert res.provenance.y_source == "USER_OVERRIDE"


def test_qars_service_z_from_zengine():
    # Test Z resolved from ZEngine for RSA-2048 (Shor vulnerable)
    asset = create_mock_asset(algorithm_name="RSA-2048")
    project = create_mock_project()
    res = evaluate_artifact_qars(asset, project)

    assert res.core_input.z_years > 0
    assert res.provenance.z_source == "Z_ENGINE"


def test_qars_service_correct_core_input_construction():
    # X=5, Y=10, Z=10, S=5, E=5
    # Sn = (5-1)/4 = 1.0, En = (5-1)/4 = 1.0
    # T = (5+10-10)/10 = 0.5
    # QARS_core = 100 * 0.5 * 1.0 * 1.0 = 50.0
    asset = create_mock_asset(algorithm_name="RSA-2048")
    project = create_mock_project(user_x_years=5, user_y_scenario="STANDARD", business_context={"factor_ratings": {"dataSensitivity": 5, "exposureRating": 5}})
    res = evaluate_artifact_qars(asset, project)

    assert res.core_input.x_years == 5.0
    assert res.core_input.y_years == 10.0
    assert res.core_input.data_sensitivity == 5.0
    assert res.core_input.exposure == 5.0


def test_qars_service_final_score_equals_core():
    asset = create_mock_asset(algorithm_name="RSA-2048")
    project = create_mock_project()
    res = evaluate_artifact_qars(asset, project)

    assert res.final_score >= res.base_score
    assert res.final_score <= 100.0
    assert sum(res.adjustments.values()) >= 0.0



def test_qars_service_provenance_preserved():
    asset = create_mock_asset(
        extra_metadata={"context_overrides": {"x_years": 8.0, "data_sensitivity": 4.0, "exposure_rating": 4.0}}
    )
    project = create_mock_project()
    res = evaluate_artifact_qars(asset, project)

    prov = res.provenance
    assert prov.x_source == "ARTIFACT_EVIDENCE"
    assert prov.s_source == "ARTIFACT_EVIDENCE"
    assert prov.e_source == "ARTIFACT_EVIDENCE"
    assert prov.z_source == "Z_ENGINE"


def test_qars_service_missing_x_fails(monkeypatch):
    asset = create_mock_asset()
    project = create_mock_project()
    import app.qars.service as qars_srv
    monkeypatch.setattr(
        qars_srv,
        "resolve_effective_artifact_context",
        lambda a, p, db: {"x_years": 0, "data_sensitivity": 4, "exposure": "INTERNAL", "sources": {}}
    )

    with pytest.raises(QARSValidationError) as excinfo:
        evaluate_artifact_qars(asset, project)
    assert "x_years" in str(excinfo.value)


def test_qars_service_missing_y_fails(monkeypatch):
    asset = create_mock_asset()
    project = create_mock_project()
    import app.qars.service as qars_srv
    class BadYEngine:
        def evaluate_y(self, user_scenario=None):
            return {"value_years": -1, "source": "INVALID"}

    monkeypatch.setattr(qars_srv, "YEngine", BadYEngine)

    with pytest.raises(QARSValidationError) as excinfo:
        evaluate_artifact_qars(asset, project)
    assert "y_years" in str(excinfo.value)


def test_qars_service_missing_z_returns_unconfigured():
    aes_asset = create_mock_asset(algorithm_name="AES-256-GCM")
    project = create_mock_project()

    res = evaluate_artifact_qars(aes_asset, project)
    assert res.level == QARSLevel.UNCONFIGURED
    assert res.final_score is None
    assert res.base_score is None
    assert "z_years" in getattr(res.explanation, "missing_evidence", res.explanation.get("missing_evidence") if isinstance(res.explanation, dict) else [])
    assert res.z_uncertainty is not None
    assert res.z_uncertainty.z_central is None


def test_qars_service_missing_s_fails(monkeypatch):
    asset = create_mock_asset()
    project = create_mock_project()
    import app.qars.service as qars_srv
    monkeypatch.setattr(
        qars_srv,
        "resolve_effective_artifact_context",
        lambda a, p, db: {"x_years": 5, "data_sensitivity": None, "exposure": "INTERNAL", "sources": {}}
    )

    with pytest.raises(QARSValidationError) as excinfo:
        evaluate_artifact_qars(asset, project)
    assert "data_sensitivity" in str(excinfo.value)


def test_qars_service_missing_e_fails(monkeypatch):
    import app.services.business_criticality_service as bcs
    monkeypatch.setattr(bcs, "DEFAULT_RATINGS", {})
    asset = create_mock_asset()
    project = create_mock_project(business_context={})

    with pytest.raises(QARSValidationError) as excinfo:
        evaluate_artifact_qars(asset, project)
    assert "exposure" in str(excinfo.value)


def test_qars_service_no_demo_values_substituted():
    aes_asset = create_mock_asset(algorithm_name="AES-256-GCM")
    project = create_mock_project()

    res = evaluate_artifact_qars(aes_asset, project)
    assert res.final_score is None
    assert res.level == QARSLevel.UNCONFIGURED


def test_qars_service_artifact_identity_preserved():
    asset = create_mock_asset(asset_id="custom-artifact-uuid-99")
    project = create_mock_project()
    res = evaluate_artifact_qars(asset, project)

    assert res.asset_id == "custom-artifact-uuid-99"


def test_qars_service_project_identity_preserved():
    asset = create_mock_asset()
    project = create_mock_project(project_id="custom-project-uuid-77")
    res = evaluate_artifact_qars(asset, project)

    assert res.project_id == "custom-project-uuid-77"


def test_qars_service_scan_identity_preserved():
    asset = create_mock_asset(scan_id="custom-scan-uuid-33")
    project = create_mock_project()
    res = evaluate_artifact_qars(asset, project)

    assert res.scan_id == "custom-scan-uuid-33"


def test_qars_service_custom_thresholds():
    custom_cfg = QARSConfig(low_max=10.0, medium_max=30.0, high_max=60.0, critical_max=100.0)
    asset = create_mock_asset()
    project = create_mock_project(user_x_years=5, user_y_scenario="STANDARD", business_context={"factor_ratings": {"dataSensitivity": 3, "exposureRating": 3}})
    # QARS Core score = 12.5 -> with low_max=10.0, medium_max=30.0 -> MEDIUM
    res = evaluate_artifact_qars(asset, project, config=custom_cfg)

    assert res.base_score == 12.5
    assert res.level == QARSLevel.MEDIUM


def test_qars_service_phase4_end_to_end():
    asset = create_mock_asset()
    project = create_mock_project()
    res = evaluate_artifact_qars(asset, project)

    assert res.migration_complexity is not None
    assert res.z_uncertainty is not None
    assert res.z_uncertainty.status == "POINT_ESTIMATE_ONLY"
    assert res.z_uncertainty.z_central == res.core_input.z_years
    assert res.explanation.migration_complexity is not None
    assert res.explanation.z_uncertainty is not None

