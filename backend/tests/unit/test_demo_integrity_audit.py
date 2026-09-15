import pytest
from app.recommend.engine import RecommendationEngine
from app.migration.effort_estimator import classify_migration_effort, estimate_migration_effort
from app.models.enums import CryptoPurpose, QuantumSafety, MigrationProfile


def test_recommendation_tradeoffs_no_synthetic_person_days():
    """Verify recommendation tradeoffs contain no synthetic person-day figures or fake benchmarks."""
    engine = RecommendationEngine()
    
    # 1. Key Establishment (ML-KEM)
    rec_kem = engine.generate_recommendation(
        algorithm_name="ECDH-P256",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        profile=MigrationProfile.BALANCED
    )
    cost_impact = rec_kem.get("tradeoffs", {}).get("cost_impact", "")
    perf_notes = rec_kem.get("tradeoffs", {}).get("performance_notes", "")
    
    assert "person-days" not in cost_impact.lower()
    assert "person_days" not in cost_impact.lower()
    assert "$" not in cost_impact
    assert "~0.05ms" not in perf_notes

    # 2. Digital Signature (ML-DSA)
    rec_dsa = engine.generate_recommendation(
        algorithm_name="RSA-2048",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        profile=MigrationProfile.SECURITY_FIRST
    )
    cost_impact_dsa = rec_dsa.get("tradeoffs", {}).get("cost_impact", "")
    perf_notes_dsa = rec_dsa.get("tradeoffs", {}).get("performance_notes", "")

    assert "person-days" not in cost_impact_dsa.lower()
    assert "person_days" not in cost_impact_dsa.lower()
    assert "$" not in cost_impact_dsa
    assert "~0.1ms" not in perf_notes_dsa


def test_evidence_backed_effort_classification_intact():
    """Verify LOW, MEDIUM, HIGH qualitative effort classification and evidence factors remain fully intact."""
    # Small low-impact asset
    low_res = classify_migration_effort(
        affected_assets_count=1,
        affected_files_count=1,
        blast_radius_affected_nodes=1,
        vendor_dependency_count=0,
        pki_cert_dependency_count=0,
        business_criticality_score=20.0
    )
    assert low_res["effort_level"] == "LOW"
    assert len(low_res["evidence_factors"]) >= 1

    # Large complex high-impact asset
    high_res = classify_migration_effort(
        affected_assets_count=20,
        affected_files_count=15,
        blast_radius_affected_nodes=25,
        vendor_dependency_count=3,
        pki_cert_dependency_count=2,
        business_criticality_score=90.0
    )
    assert high_res["effort_level"] == "HIGH"
    assert len(high_res["evidence_factors"]) >= 3
    for factor in high_res["evidence_factors"]:
        assert "$" not in factor


def test_no_synthetic_cost_claims_in_recommendations():
    """Verify recommendations present qualitative cost levels without fake numerical dollar figures."""
    engine = RecommendationEngine()
    recs = [
        engine.generate_recommendation("RSA-2048", CryptoPurpose.DIGITAL_SIGNATURE, QuantumSafety.QUANTUM_VULNERABLE),
        engine.generate_recommendation("ECDH-P256", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE),
        engine.generate_recommendation("AES-256-GCM", CryptoPurpose.ENCRYPTION, QuantumSafety.QUANTUM_SAFE)
    ]

    for rec in recs:
        tradeoffs = rec.get("tradeoffs", {})
        cost_impact = tradeoffs.get("cost_impact", "")
        cost_level = tradeoffs.get("cost_level", "")

        assert "$" not in cost_impact
        assert cost_level in ("LOW", "MODERATE", "HIGH", "ZERO", "UNKNOWN")
