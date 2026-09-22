import pytest
from pathlib import Path
from app.qars.calibration import (
    QARSCalibrationRecord,
    QARSCalibrationProvider,
    get_default_calibration_provider,
    get_default_calibration_file_path,
)
from app.qars.algorithm import evaluate_algorithm_risk


def test_1_dataset_loads_successfully():
    provider = get_default_calibration_provider()
    assert provider is not None
    assert len(provider.records) > 0
    assert provider.version == "SENTRIQ QARS Prototype Heuristic Calibration v1"


def test_2_dataset_schema_validation():
    path = get_default_calibration_file_path()
    assert path.is_file()
    provider = QARSCalibrationProvider(json_path=path)
    assert len(provider.records) >= 10


def test_3_invalid_va_rejected():
    record = QARSCalibrationRecord(
        canonical_algorithm="TEST",
        vulnerability_factor=1.5,
        security_strength_factor=0.5,
    )
    with pytest.raises(ValueError, match="Invalid vulnerability_factor"):
        record.validate_factors()


def test_4_invalid_sp_rejected():
    record = QARSCalibrationRecord(
        canonical_algorithm="TEST",
        vulnerability_factor=0.5,
        security_strength_factor=-0.2,
    )
    with pytest.raises(ValueError, match="Invalid security_strength_factor"):
        record.validate_factors()


def test_5_exact_rsa2048_resolution():
    provider = get_default_calibration_provider()
    rec = provider.resolve_calibration("RSA", parameter=2048)
    assert rec.calibration_status == "CONFIGURED"
    assert rec.vulnerability_factor == 0.90
    assert rec.security_strength_factor == 0.80
    assert rec.confidence == "PROVISIONAL"


def test_6_exact_rsa3072_resolution():
    provider = get_default_calibration_provider()
    rec = provider.resolve_calibration("RSA", parameter=3072)
    assert rec.calibration_status == "CONFIGURED"
    assert rec.vulnerability_factor == 0.90
    assert rec.security_strength_factor == 0.60
    assert rec.confidence == "PROVISIONAL"


def test_7_exact_ecdsa_p256_resolution():
    provider = get_default_calibration_provider()
    rec = provider.resolve_calibration("ECDSA", parameter="P256")
    assert rec.calibration_status == "CONFIGURED"
    assert rec.vulnerability_factor == 0.95
    assert rec.security_strength_factor == 0.80
    assert rec.confidence == "PROVISIONAL"


def test_8_exact_ecdh_p256_resolution():
    provider = get_default_calibration_provider()
    rec = provider.resolve_calibration("ECDH", parameter="P256")
    assert rec.calibration_status == "CONFIGURED"
    assert rec.vulnerability_factor == 0.95
    assert rec.security_strength_factor == 0.80
    assert rec.confidence == "PROVISIONAL"


def test_9_exact_aes256_resolution():
    provider = get_default_calibration_provider()
    rec = provider.resolve_calibration("AES", parameter=256)
    assert rec.calibration_status == "CONFIGURED"
    assert rec.vulnerability_factor == 0.10
    assert rec.security_strength_factor == 0.20
    assert rec.confidence == "PROVISIONAL"


def test_10_sha256_resolution():
    provider = get_default_calibration_provider()
    rec = provider.resolve_calibration("SHA-256", parameter=None)
    assert rec.calibration_status == "CONFIGURED"
    assert rec.vulnerability_factor == 0.15
    assert rec.security_strength_factor == 0.20
    assert rec.confidence == "PROVISIONAL"


def test_11_canonical_fallback():
    provider = get_default_calibration_provider()
    rec = provider.resolve_calibration("RSA", parameter=8192)
    assert rec.calibration_status == "CONFIGURED"
    assert rec.vulnerability_factor == 0.90
    assert rec.security_strength_factor == 0.70
    assert rec.confidence == "PROVISIONAL"


def test_12_unknown_algorithm_unconfigured():
    provider = get_default_calibration_provider()
    rec = provider.resolve_calibration("SuperCipher99")
    assert rec.calibration_status == "UNCONFIGURED"
    assert rec.confidence == "INSUFFICIENT_EVIDENCE"
    assert rec.vulnerability_factor is None
    assert rec.security_strength_factor is None


def test_13_missing_parameter_canonical_fallback():
    provider = get_default_calibration_provider()
    rec = provider.resolve_calibration("RSA", parameter=None)
    assert rec.calibration_status == "CONFIGURED"
    assert rec.parameter is None


def test_14_calibration_provenance_preserved():
    provider = get_default_calibration_provider()
    rec = provider.resolve_calibration("RSA", parameter=2048)
    assert rec.source == "SENTRIQ_PROTOTYPE_HEURISTIC"
    assert rec.source != "SENTRIQ_PQC_RESEARCH_2026"


def test_15_calibration_version_preserved():
    provider = get_default_calibration_provider()
    rec = provider.resolve_calibration("AES", parameter=256)
    assert rec.calibration_version == "SENTRIQ QARS Prototype Heuristic Calibration v1"


def test_16_methodology_preserved():
    provider = get_default_calibration_provider()
    rec = provider.resolve_calibration("ECDSA", parameter="P256")
    assert "prototype normalized vulnerability factor" in rec.methodology
    assert "calibration-policy values" in rec.methodology


def test_17_configured_profile_numeric_aqr():
    res = evaluate_algorithm_risk("RSA-2048")
    assert res.calibration_status == "CONFIGURED"
    assert res.vulnerability_factor == 0.90
    assert res.security_strength_factor == 0.80
    assert res.aqr_score == pytest.approx(0.72)
    assert res.confidence == "PROVISIONAL"
    assert res.calibration_version == "SENTRIQ QARS Prototype Heuristic Calibration v1"
    assert res.calibration_source == "SENTRIQ_PROTOTYPE_HEURISTIC"


def test_18_unconfigured_profile_aqr_none():
    res = evaluate_algorithm_risk("UnknownAlgo999")
    assert res.calibration_status == "UNCONFIGURED"
    assert res.aqr_score is None


def test_19_unconfigured_profile_insufficient_evidence():
    res = evaluate_algorithm_risk("UnknownAlgo999")
    assert res.confidence == "INSUFFICIENT_EVIDENCE"


def test_20_no_calibration_numbers_in_python_business_logic():
    qars_dir = Path(__file__).parent.parent.parent / "app" / "qars"
    for py_file in qars_dir.glob("*.py"):
        if py_file.name == "calibration.py":
            continue
        content = py_file.read_text(encoding="utf-8")
        assert "vulnerability_factor = 0." not in content
        assert "security_strength_factor = 0." not in content


def test_21_no_unsupported_research_source_claim():
    json_path = get_default_calibration_file_path()
    content = json_path.read_text(encoding="utf-8")
    assert "SENTRIQ_PQC_RESEARCH_2026" not in content
    assert "authoritative" not in content.lower()
