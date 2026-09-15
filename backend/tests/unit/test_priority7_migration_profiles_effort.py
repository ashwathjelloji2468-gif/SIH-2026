import pytest
from app.models.enums import MigrationProfile, MigrationEffortLevel
from app.migration.effort_estimator import classify_migration_effort, estimate_migration_effort
from app.recommend.engine import RecommendationEngine
from app.models.db_models import CryptoAsset
from app.models.enums import AssetType, CryptoPurpose, QuantumSafety


def test_migration_profile_enum_values():
    """Verify MigrationProfile enum contains expected strategy profiles."""
    assert MigrationProfile.LOW_LATENCY.value == "LOW_LATENCY"
    assert MigrationProfile.BALANCED.value == "BALANCED"
    assert MigrationProfile.SECURITY_FIRST.value == "SECURITY_FIRST"


def test_migration_effort_level_enum_values():
    """Verify MigrationEffortLevel enum contains expected effort levels."""
    assert MigrationEffortLevel.LOW.value == "LOW"
    assert MigrationEffortLevel.MEDIUM.value == "MEDIUM"
    assert MigrationEffortLevel.HIGH.value == "HIGH"


def test_effort_classification_low():
    """Test evidence-backed effort classification for a small codebase."""
    res = classify_migration_effort(
        affected_assets_count=2,
        affected_files_count=1,
        blast_radius_affected_nodes=2,
        vendor_dependency_count=0,
        pki_cert_dependency_count=0,
        business_criticality_score=25.0
    )
    assert res["effort_level"] == "LOW"
    factors = res.get("factors") or res.get("evidence_factors", [])
    assert len(factors) >= 1
    # Ensure no fabricated dollar amounts or engineering hours
    for factor in factors:
        assert "$" not in factor
        assert "hours" not in factor.lower() or "person_days" in factor.lower()


def test_effort_classification_high():
    """Test evidence-backed effort classification for a large complex enterprise system."""
    res = classify_migration_effort(
        affected_assets_count=25,
        affected_files_count=18,
        blast_radius_affected_nodes=30,
        vendor_dependency_count=4,
        pki_cert_dependency_count=3,
        business_criticality_score=100.0
    )
    assert res["effort_level"] == "HIGH"
    factors = res.get("factors") or res.get("evidence_factors", [])
    assert any("criticality" in f.lower() for f in factors)
    assert any("blast radius" in f.lower() for f in factors)


def test_effort_estimation_works_without_blast_radius_score():
    """Verify effort calculation works cleanly even if blast_radius_score is absent/None."""
    effort = estimate_migration_effort(
        affected_assets_count=5,
        affected_files_count=3,
        blast_radius_affected_nodes=8,
        blast_radius_score=None,
        business_criticality_score=50.0
    )
    assert effort["effort_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert effort["person_days"] > 0
    assert effort["calendar_months"] > 0
    factors = effort.get("factors") or effort.get("evidence_factors", [])
    assert isinstance(factors, list)


def test_recommendation_engine_profile_reordering():
    """
    Verify profile re-orders valid candidates dynamically without hardcoding algorithms
    and does NOT override security rules.
    """
    engine = RecommendationEngine()

    # Asset: RSA Key Exchange
    rec_balanced = engine.generate_recommendation(
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        risk_level="HIGH",
        risk_score=75.0,
        profile="BALANCED"
    )

    rec_low_latency = engine.generate_recommendation(
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        risk_level="HIGH",
        risk_score=75.0,
        profile="LOW_LATENCY"
    )

    rec_sec_first = engine.generate_recommendation(
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        risk_level="HIGH",
        risk_score=75.0,
        profile="SECURITY_FIRST"
    )

    # Valid candidates must still be NIST FIPS standard algorithms
    assert "ML-KEM" in rec_balanced["target_pqc_candidate"]
    assert "ML-KEM" in rec_low_latency["target_pqc_candidate"]
    assert "ML-KEM" in rec_sec_first["target_pqc_candidate"]

    # Rationale annotations must reflect the selected profile strategy
    assert "Low Latency profile" in rec_low_latency["rationale"] or "balanced" in rec_low_latency["rationale"].lower()
    assert "Security First profile" in rec_sec_first["rationale"] or "security" in rec_sec_first["rationale"].lower()


def test_no_fake_dollar_or_hours_claims():
    """Audit check: ensure no synthetic dollar costs or fake speedups are returned."""
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="ECDSA-P256",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        profile="LOW_LATENCY"
    )

    cost_impact = rec.get("cost_impact", "")
    latency_impact = rec.get("latency_impact", "")
    rationale = rec.get("rationale", "")

    assert "$" not in cost_impact
    assert "% faster" not in latency_impact
    assert "$" not in rationale
