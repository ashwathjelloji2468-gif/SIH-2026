import pytest
from app.qars.objectives import resolve_security_objectives
from app.qars.algorithm import evaluate_algorithm_risk
from app.qars.models import SecurityObjectiveResult


def test_purpose_encryption_mapping():
    res = resolve_security_objectives("AES-256", purpose="ENCRYPTION")
    assert res.objectives == ["confidentiality"]
    assert res.purpose_used == "ENCRYPTION"
    assert res.source == "EXPLICIT_PURPOSE"


def test_purpose_key_establishment_mapping():
    res = resolve_security_objectives("ECDH", purpose="KEY_ESTABLISHMENT")
    assert res.objectives == ["confidentiality", "key_establishment"]
    assert res.purpose_used == "KEY_ESTABLISHMENT"
    assert res.source == "EXPLICIT_PURPOSE"


def test_purpose_signature_mapping():
    res_sig = resolve_security_objectives("ECDSA-P256", purpose="SIGNATURE")
    assert res_sig.objectives == ["integrity", "authentication"]

    res_dsig = resolve_security_objectives("RSA-2048", purpose="DIGITAL_SIGNATURE")
    assert res_dsig.objectives == ["integrity", "authentication"]


def test_purpose_hashing_mapping():
    res = resolve_security_objectives("SHA-256", purpose="HASHING")
    assert res.objectives == ["integrity"]


def test_purpose_mac_mapping():
    res = resolve_security_objectives("HMAC-SHA256", purpose="MAC")
    assert res.objectives == ["integrity", "authentication"]


def test_purpose_password_derivation_mapping():
    res = resolve_security_objectives("PBKDF2", purpose="PASSWORD_DERIVATION")
    assert res.objectives == ["confidentiality"]


def test_purpose_unknown_mapping():
    res = resolve_security_objectives("UnknownAlgo99", purpose=None)
    assert res.purpose_used == "UNKNOWN"
    assert res.source == "UNKNOWN"


def test_multiple_objectives_ordering():
    # SIGNATURE yields integrity and authentication
    res = resolve_security_objectives("ECDSA", purpose="SIGNATURE")
    # Order must match canonical priority: confidentiality, integrity, authentication, key_establishment
    assert res.objectives == ["integrity", "authentication"]

    # KEY_ESTABLISHMENT yields confidentiality and key_establishment
    res_ke = resolve_security_objectives("ECDH", purpose="KEY_ESTABLISHMENT")
    assert res_ke.objectives == ["confidentiality", "key_establishment"]


def test_explicit_purpose_precedence():
    # RSA normally infers SIGNATURE, but explicit ENCRYPTION overrides
    res = resolve_security_objectives("RSA-2048", purpose="ENCRYPTION")
    assert res.objectives == ["confidentiality"]
    assert res.source == "EXPLICIT_PURPOSE"


def test_rule_inferred_purpose_fallback():
    # Omit explicit purpose for AES-256 -> rules map to ENCRYPTION -> confidentiality
    res = resolve_security_objectives("AES-256")
    assert res.source == "DETERMINED_PURPOSE"
    assert res.purpose_used in ["ENCRYPTION", "SYMMETRIC_ENCRYPTION"]
    assert "confidentiality" in res.objectives


def test_catalog_purpose_fallback():
    # If rule engine returns UNKNOWN but catalog has purpose
    res = resolve_security_objectives("RSA", purpose=None)
    assert res.source in ["DETERMINED_PURPOSE", "ALGORITHM_KNOWLEDGE_BASE"]
    assert len(res.objectives) > 0


def test_objective_resolution_source_tracking():
    res_exp = resolve_security_objectives("AES-256", purpose="ENCRYPTION")
    assert res_exp.source == "EXPLICIT_PURPOSE"

    res_rule = resolve_security_objectives("AES-256")
    assert res_rule.source in ["DETERMINED_PURPOSE", "ALGORITHM_KNOWLEDGE_BASE"]

    res_unk = resolve_security_objectives("xyz123999")
    assert res_unk.source == "UNKNOWN"


def test_security_objectives_attached_to_algorithm_risk():
    alg_risk = evaluate_algorithm_risk("RSA-2048", purpose="SIGNATURE")
    assert alg_risk.security_objectives == ["integrity", "authentication"]
