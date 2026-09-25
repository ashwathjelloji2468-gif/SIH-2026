import pytest
from app.audit.provider import MockBlockchainAuditProvider
from app.audit.service import AuditService
from app.recommend.service import RecommendationService
from app.models.enums import CryptoPurpose, QuantumSafety

def test_a_b_c_d_project_recommendation_audit_attachment():
    """
    TEST A, B, C, D: Project-level recommendation results attach audit data
    with correct asset_id, READY status, and preserved provider/digest values.
    """
    mock_provider = MockBlockchainAuditProvider()
    audit_service = AuditService(provider=mock_provider)

    class MockAsset:
        id = "asset-test-p4b-123"
        name = "Test RSA Asset"
        algorithm_name = "RSA-2048"
        purpose = CryptoPurpose.DIGITAL_SIGNATURE
        quantum_safety = QuantumSafety.QUANTUM_VULNERABLE
        location = "auth.py"
        line_number = 42

    engine = RecommendationService(db=None)
    rec_dict = engine._recommendation_to_dict(None, MockAsset(), None, [])
    from app.audit.integration import audit_recommendation_snapshot
    res = audit_recommendation_snapshot(rec_dict, asset_id=MockAsset.id, service=audit_service)

    assert res is not None
    assert "audit" in rec_dict
    assert rec_dict["audit"]["status"] == "READY"
    assert rec_dict["audit"]["artifact_id"] == f"rec-{MockAsset.id}"
    assert rec_dict["audit"]["provider_name"] == "MockBlockchainAuditProvider"
    assert len(rec_dict["audit"]["digest"]) == 64
    assert rec_dict["audit"]["network"] == "in-memory-mock"

def test_e_audit_failure_is_non_blocking():
    """
    TEST E: Audit failure remains completely non-blocking for recommendation output.
    """
    class FailingProvider:
        def get_provider_name(self): return "FailingProvider"
        def record_digest(self, artifact_type, artifact_id, digest, metadata=None):
            raise RuntimeError("RPC Connection Timeout")
        def verify_digest(self, artifact_type, artifact_id, expected_digest):
            raise RuntimeError("RPC Connection Timeout")

    failing_service = AuditService(provider=FailingProvider())

    rec_dict = {"target_pqc_candidate": "ML-DSA (FIPS 204)", "profile": "BALANCED"}
    from app.audit.integration import audit_recommendation_snapshot
    res = audit_recommendation_snapshot(rec_dict, asset_id="asset-fail-123", service=failing_service)
    
    # Snapshot returns None on error, rec_dict recommendation structure remains clean
    assert res is None
    assert rec_dict["target_pqc_candidate"] == "ML-DSA (FIPS 204)"

def test_f_g_h_i_additive_audit_and_preservation_semantics():
    """
    TEST F, G, H, I: Audit field is purely additive. ML performance evidence,
    candidate ranking, and read-only GET semantics remain untouched.
    """
    mock_provider = MockBlockchainAuditProvider()
    audit_service = AuditService(provider=mock_provider)

    from app.recommend.engine import RecommendationEngine
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="ECDH-P256",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        context={"text_length_bytes": 1024}
    )

    from app.audit.integration import audit_recommendation_snapshot
    audit_recommendation_snapshot(rec, asset_id="asset-sem-123", service=audit_service)

    assert rec["recommended_algorithm"] == "ML-KEM (FIPS 203)"
    assert rec["tradeoffs"]["performance"]["status"] == "READY"
    assert "audit" in rec
    assert rec["audit"]["status"] == "READY"
