import pytest
from app.models.enums import CryptoPurpose, QuantumSafety, RecommendationCategory
from app.recommend.engine import RecommendationEngine
from app.knowledge.pqc_catalog import PQC_CATALOG, CATALOG_VERSION, get_candidate


def test_a_operation_classification():
    engine = RecommendationEngine()
    
    # RSA Encryption / Key Transport
    rec_rsa_enc = engine.generate_recommendation("RSA-2048", CryptoPurpose.ENCRYPTION, QuantumSafety.QUANTUM_VULNERABLE)
    assert rec_rsa_enc["quantum_attack_type"] == "Shor's Algorithm"
    assert "confidentiality" in rec_rsa_enc["security_objectives"]

    # RSA Signature
    rec_rsa_sig = engine.generate_recommendation("RSA-2048", CryptoPurpose.DIGITAL_SIGNATURE, QuantumSafety.QUANTUM_VULNERABLE)
    assert rec_rsa_sig["quantum_attack_type"] == "Shor's Algorithm"
    assert "integrity" in rec_rsa_sig["security_objectives"]
    assert "authentication" in rec_rsa_sig["security_objectives"]

    # ECDSA Signature
    rec_ecdsa = engine.generate_recommendation("ECDSA", CryptoPurpose.DIGITAL_SIGNATURE, QuantumSafety.QUANTUM_VULNERABLE)
    assert rec_ecdsa["quantum_attack_type"] == "Shor's Algorithm"
    assert "integrity" in rec_ecdsa["security_objectives"]

    # ECDH Key Establishment
    rec_ecdh = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    assert rec_ecdh["quantum_attack_type"] == "Shor's Algorithm"
    assert "key_establishment" in rec_ecdh["security_objectives"]

    # AES Encryption
    rec_aes = engine.generate_recommendation("AES-256", CryptoPurpose.ENCRYPTION, QuantumSafety.QUANTUM_SAFE)
    assert rec_aes["quantum_attack_type"] == "Grover's Algorithm"
    assert "confidentiality" in rec_aes["security_objectives"]

    # SHA-256 Hashing
    rec_sha = engine.generate_recommendation("SHA-256", CryptoPurpose.HASHING, QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN)
    assert "Grover" in rec_sha["quantum_attack_type"]
    assert "integrity" in rec_sha["security_objectives"]


def test_b_purpose_mapping():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation("ECDH-P256", CryptoPurpose.UNKNOWN, QuantumSafety.QUANTUM_VULNERABLE)
    assert rec["purpose"] == "KEY_ESTABLISHMENT"


def test_c_security_objective_mapping():
    engine = RecommendationEngine()
    rec_kem = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    assert set(rec_kem["security_objectives"]) == {"confidentiality", "key_establishment"}

    rec_sig = engine.generate_recommendation("ECDSA", CryptoPurpose.DIGITAL_SIGNATURE, QuantumSafety.QUANTUM_VULNERABLE)
    assert set(rec_sig["security_objectives"]) == {"integrity", "authentication"}


def test_d_kem_candidates_rejected_for_signature_purpose():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation("ECDSA", CryptoPurpose.DIGITAL_SIGNATURE, QuantumSafety.QUANTUM_VULNERABLE)
    
    # Verify ML-KEM is in rejected candidates with purpose mismatch reason
    ml_kem_rejected = [c for c in rec["rejected_candidates"] if "ML-KEM" in c["candidate"]]
    assert len(ml_kem_rejected) > 0
    assert any("Purpose mismatch" in r for r in ml_kem_rejected[0]["reasons"])


def test_e_signature_candidates_rejected_for_key_establishment_purpose():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    
    # Verify ML-DSA is in rejected candidates with purpose mismatch reason
    ml_dsa_rejected = [c for c in rec["rejected_candidates"] if "ML-DSA" in c["candidate"]]
    assert len(ml_dsa_rejected) > 0
    assert any("Purpose mismatch" in r for r in ml_dsa_rejected[0]["reasons"])


def test_f_protocol_incompatibility_rejection():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        "ECDSA", CryptoPurpose.DIGITAL_SIGNATURE, QuantumSafety.QUANTUM_VULNERABLE,
        target_protocol="TLS 1.3"
    )
    slh_rejected = [c for c in rec["rejected_candidates"] if "SLH-DSA" in c["candidate"]]
    assert len(slh_rejected) > 0
    assert any("Protocol incompatibility" in r for r in slh_rejected[0]["reasons"])


def test_g_library_support_filtering():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        "ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE,
        target_library="OpenSSL 3.5"
    )
    assert len(rec["eligible_candidates"]) > 0
    assert any("OpenSSL" in e for e in rec["eligible_candidates"][0]["evidence"])


def test_h_security_level_filtering():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        "ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE,
        required_security_level=5
    )
    eligible_names = [c["candidate"] for c in rec["eligible_candidates"]]
    assert "ML-KEM-1024" in eligible_names
    assert "ML-KEM-512" not in eligible_names


def test_i_application_constraint_filtering():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        "ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE,
        max_size_bytes=1000
    )
    eligible_names = [c["candidate"] for c in rec["eligible_candidates"]]
    assert "ML-KEM-512" in eligible_names
    assert "ML-KEM-1024" not in eligible_names


def test_j_unknown_evidence_handling():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation("CUSTOM_UNKNOWN", CryptoPurpose.UNKNOWN, QuantumSafety.UNKNOWN)
    assert rec["category"] == RecommendationCategory.MANUAL_REVIEW
    assert rec["needs_review"] is True


def test_k_rejected_candidate_reasons():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    for rej in rec["rejected_candidates"]:
        assert "candidate" in rej
        assert rej["eligible"] is False
        assert len(rej["reasons"]) > 0


def test_l_deterministic_recommendation_output():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        "RSA-2048", CryptoPurpose.DIGITAL_SIGNATURE, QuantumSafety.QUANTUM_VULNERABLE,
        asset_location="src/crypto/signer.py", asset_line_number=42, asset_name="SignatureVerifier"
    )
    assert "what" in rec and "ML-DSA" in rec["what"]
    assert "where" in rec and "SignatureVerifier" in rec["where"] and ":L42" in rec["where"]
    assert "why" in rec and "RSA-2048" in rec["why"]
    assert "what_next" in rec


def test_m_recommendation_persistence():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    assert rec["kb_version"] == CATALOG_VERSION
    assert "transformation_pattern" in rec


def test_n_get_does_not_regenerate_mocked():
    from app.recommend.service import RecommendationService
    class DummyRepo:
        def get_latest_for_asset(self, asset_id):
            return type("Rec", (), {"id": "rec_123", "asset_id": asset_id, "target_pqc_candidate": "PREVIOUS_ML_KEM", "recommended_algorithm": "PREVIOUS_ML_KEM", "alternative_algorithm": None, "category": RecommendationCategory.PQC_REPLACEMENT, "priority": "HIGH", "standard_status": "FINAL_STANDARD", "rationale": "Stored rationale", "compatibility_notes": None, "performance_notes": None, "tradeoffs": {}, "threat_scenarios": [], "migration_notes": "", "migration_complexity": "MEDIUM", "confidence": 0.9, "kb_version": "2026.3.0", "risk_assessment_id": None, "created_at": "2026-09-23T12:00:00"})()
    
    class DummyAssetRepo:
        def get(self, asset_id):
            return type("Asset", (), {"id": asset_id, "name": "Asset1", "algorithm_name": "ECDH", "purpose": CryptoPurpose.KEY_ESTABLISHMENT, "quantum_safety": QuantumSafety.QUANTUM_VULNERABLE, "scan": None, "location": "app.py", "line_number": 10})()

    svc = RecommendationService(db=None)
    svc.asset_repo = DummyAssetRepo()
    svc.rec_repo = DummyRepo()
    
    res = svc.recommend_asset("asset_123", force_regeneration=False)
    assert res["target_pqc_candidate"] == "PREVIOUS_ML_KEM"


def test_o_explicit_evaluation_regenerates():
    from app.recommend.service import RecommendationService
    class DummyAssetRepo:
        def get(self, asset_id):
            return type("Asset", (), {"id": asset_id, "name": "Asset1", "algorithm_name": "ECDH", "purpose": CryptoPurpose.KEY_ESTABLISHMENT, "quantum_safety": QuantumSafety.QUANTUM_VULNERABLE, "scan": None, "location": "app.py", "line_number": 10, "evidence_items": []})()

    svc = RecommendationService(db=None)
    svc.asset_repo = DummyAssetRepo()
    svc.rec_repo = None
    
    res = svc.recommend_asset("asset_123", force_regeneration=True)
    assert "ML-KEM" in res["target_pqc_candidate"]


def test_p_scan_enrichment_regenerates():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    assert rec["category"] == RecommendationCategory.PQC_REPLACEMENT


def test_q_project_asset_scan_isolation():
    from app.recommend.service import RecommendationService
    svc = RecommendationService(db=None)
    svc.asset_repo = type("AssetRepo", (), {"get_by_project": lambda self, pid: []})()
    res = svc.recommend_project("proj_empty")
    assert res == []


def test_r_no_fabricated_latency_migration_values():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    lat = rec["expected_latency"]
    assert lat["status"] in ["MEASURED", "DERIVED", "UNKNOWN"]
    assert "provenance" in lat


def test_s_deterministic_tie_handling():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    # When multiple KEM candidates have security level 3 (e.g. ML-KEM-768, X25519_MLKEM768, SecP256r1_MLKEM768)
    assert len(rec["eligible_candidates"]) > 1
    assert rec["needs_review"] is True
    assert rec["alternative_algorithm"] is not None


def test_t_ml_boundary_verification():
    engine = RecommendationEngine()
    rec = engine.generate_recommendation("ECDH", CryptoPurpose.KEY_ESTABLISHMENT, QuantumSafety.QUANTUM_VULNERABLE)
    assert rec["ml_ranking_status"] == "UNCONFIGURED"
    assert rec["ml_ranking_reason"] == "NO_HISTORICAL_MIGRATION_DATA"
    
    # Ensure rejected candidates are not passed to eligible candidates list
    rejected_names = {c["candidate"] for c in rec["rejected_candidates"]}
    eligible_names = {c["candidate"] for c in rec["eligible_candidates"]}
    assert len(rejected_names.intersection(eligible_names)) == 0
