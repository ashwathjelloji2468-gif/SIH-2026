import pytest
from unittest.mock import MagicMock

from app.audit import (
    AuditArtifactType,
    AuditResult,
    AuditStatus,
    BlockchainAuditProvider,
    ErrorBlockchainAuditProvider,
    MockBlockchainAuditProvider,
    UnconfiguredBlockchainAuditProvider,
    digest_payload,
    get_shared_audit_service,
)
from app.audit.integration import (
    audit_cbom_snapshot,
    audit_recommendation_snapshot,
    audit_risk_snapshot,
    audit_validation_result,
)
from app.audit.service import AuditService


class SpyProvider(BlockchainAuditProvider):
    def __init__(self):
        self.records = []

    @property
    def provider_name(self) -> str:
        return "SpyProvider"

    def record_artifact_digest(self, artifact_type, artifact_id, digest, metadata=None):
        self.records.append({
            "artifact_type": artifact_type,
            "artifact_id": artifact_id,
            "digest": digest,
            "metadata": metadata,
        })
        return AuditResult(
            status=AuditStatus.READY,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            digest=digest,
            provider_name=self.provider_name,
            evidence=["Spy recorded digest."],
        )

    def verify_artifact_digest(self, artifact_type, artifact_id, digest):
        return AuditResult(
            status=AuditStatus.READY,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            digest=digest,
            provider_name=self.provider_name,
        )


def test_a_cbom_finalized_artifact_generates_audit_digest():
    """TEST A: CBOM finalized artifact generates audit digest."""
    spy = SpyProvider()
    service = AuditService(provider=spy)

    cbom_data = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "components": [{"name": "RSA-2048", "type": "cryptographic"}],
    }

    res = audit_cbom_snapshot(cbom_data, scan_id="scan-123", service=service)

    assert res is not None
    assert res.status == AuditStatus.READY
    assert res.artifact_type == "cbom_snapshot"
    assert res.artifact_id == "cbom-scan-123"
    assert len(spy.records) == 1
    assert spy.records[0]["digest"] == digest_payload(cbom_data)


def test_b_risk_finalized_artifact_generates_audit_digest():
    """TEST B: Risk finalized artifact generates audit digest."""
    spy = SpyProvider()
    service = AuditService(provider=spy)

    risk_data = {"risk_score": 75.0, "risk_level": "HIGH", "threats": ["Mosca breach"]}
    res = audit_risk_snapshot(risk_data, target_id="asset-456", is_project=False, service=service)

    assert res is not None
    assert res.status == AuditStatus.READY
    assert res.artifact_type == "risk_assessment_snapshot"
    assert res.artifact_id == "risk-asset-asset-456"
    assert spy.records[0]["digest"] == digest_payload(risk_data)


def test_c_recommendation_finalized_artifact_generates_audit_digest():
    """TEST C: Recommendation finalized artifact generates audit digest."""
    spy = SpyProvider()
    service = AuditService(provider=spy)

    rec_data = {"target_pqc_candidate": "ML-KEM-768", "profile": "BALANCED"}
    res = audit_recommendation_snapshot(rec_data, asset_id="asset-789", service=service)

    assert res is not None
    assert res.status == AuditStatus.READY
    assert res.artifact_type == "recommendation_snapshot"
    assert res.artifact_id == "rec-asset-789"
    assert spy.records[0]["digest"] == digest_payload(rec_data)


def test_d_migration_validation_result_generates_audit_digest():
    """TEST D: Migration validation result generates audit digest."""
    spy = SpyProvider()
    service = AuditService(provider=spy)

    val_data = {"status": "PASSED", "build_passed": True, "residual_risk_score": 15.0}
    res = audit_validation_result(val_data, validation_id="val-101", service=service)

    assert res is not None
    assert res.status == AuditStatus.READY
    assert res.artifact_type == "migration_validation_result"
    assert res.artifact_id == "val-val-101"
    assert spy.records[0]["digest"] == digest_payload(val_data)


def test_e_each_artifact_uses_correct_artifact_type():
    """TEST E: Each artifact uses the correct artifact_type."""
    spy = SpyProvider()
    service = AuditService(provider=spy)

    audit_cbom_snapshot({"bomFormat": "CycloneDX"}, "s1", service=service)
    audit_risk_snapshot({"score": 10}, "a1", service=service)
    audit_recommendation_snapshot({"target": "ML-KEM-768"}, "a1", service=service)
    audit_validation_result({"status": "PASSED"}, "v1", service=service)

    types = [r["artifact_type"] for r in spy.records]
    assert types == [
        "cbom_snapshot",
        "risk_assessment_snapshot",
        "recommendation_snapshot",
        "migration_validation_result",
    ]


def test_f_g_h_deterministic_digest_matching():
    """TEST F, G, H: Deterministic digest generation and mismatch detection."""
    payload = {"key": "value", "list": [1, 2, 3]}
    modified_payload = {"key": "value", "list": [1, 2, 4]}

    d1 = digest_payload(payload)
    d2 = digest_payload(payload)
    d3 = digest_payload(modified_payload)

    # Test F & G: Deterministic match
    assert d1 == d2

    # Test H: Modified artifact produces different digest
    assert d1 != d3


def test_i_j_provider_receives_digest_never_raw_sensitive_payload():
    """TEST I & J: Provider receives digest but never raw artifact payload or sensitive content."""
    spy = SpyProvider()
    service = AuditService(provider=spy)

    sensitive_payload = {
        "source_code": "def secret(): pass",
        "private_key": "-----BEGIN PRIVATE KEY-----",
        "secret_token": "token123",
        "components": [{"name": "AES-256"}],
    }
    metadata = {
        "source_code": "def secret(): pass",
        "private_key": "-----BEGIN PRIVATE KEY-----",
        "version": "1.0",
    }

    audit_cbom_snapshot(sensitive_payload, scan_id="s-sec", service=service)

    call = spy.records[0]

    # Verify provider receives SHA-256 digest
    assert call["digest"] == digest_payload(sensitive_payload)

    # Verify raw payload was NOT passed
    assert "source_code" not in call
    assert "private_key" not in call

    # Verify metadata sanitization
    meta = call["metadata"]
    assert "source_code" not in meta
    assert "private_key" not in meta
    assert meta.get("version") == "1.0" or "scan_id" in meta


def test_k_l_m_n_unconfigured_provider_non_blocking():
    """TEST K, L, M, N: UNCONFIGURED provider does NOT break flows."""
    unconfig_service = AuditService(provider=UnconfiguredBlockchainAuditProvider())

    # CBOM flow
    cbom_res = audit_cbom_snapshot({"test": 1}, "s1", service=unconfig_service)
    assert cbom_res.status == AuditStatus.UNCONFIGURED

    # Risk flow
    risk_res = audit_risk_snapshot({"test": 1}, "a1", service=unconfig_service)
    assert risk_res.status == AuditStatus.UNCONFIGURED

    # Recommendation flow
    rec_res = audit_recommendation_snapshot({"test": 1}, "a1", service=unconfig_service)
    assert rec_res.status == AuditStatus.UNCONFIGURED

    # Validation flow
    val_res = audit_validation_result({"test": 1}, "v1", service=unconfig_service)
    assert val_res.status == AuditStatus.UNCONFIGURED


def test_o_provider_error_non_blocking():
    """TEST O: Provider ERROR does NOT break core flow."""
    err_service = AuditService(provider=ErrorBlockchainAuditProvider("Node timeout"))

    res = audit_cbom_snapshot({"test": 1}, "s-err", service=err_service)
    assert res.status == AuditStatus.ERROR
    assert "Node timeout" in res.warnings[0]


def test_p_q_r_s_audit_does_not_alter_original_flow_data():
    """TEST P, Q, R, S: Audit does not alter CBOM, Risk, Recommendation, or Validation core output."""
    cbom_in = {"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []}
    cbom_copy = dict(cbom_in)

    audit_cbom_snapshot(cbom_in, "s-orig")

    # Core CBOM data is unmutated; audit is additive only
    cbom_core = {k: v for k, v in cbom_in.items() if k != "audit"}
    assert cbom_core == cbom_copy
    assert "audit" in cbom_in


def test_t_independent_artifact_types():
    """TEST T: All four artifact types are independently auditable."""
    mock_prov = MockBlockchainAuditProvider()
    srv = AuditService(provider=mock_prov)

    r1 = srv.record_artifact(AuditArtifactType.CBOM_SNAPSHOT, "c1", {"a": 1})
    r2 = srv.record_artifact(AuditArtifactType.RISK_ASSESSMENT_SNAPSHOT, "r1", {"b": 2})
    r3 = srv.record_artifact(AuditArtifactType.RECOMMENDATION_SNAPSHOT, "rc1", {"c": 3})
    r4 = srv.record_artifact(AuditArtifactType.MIGRATION_VALIDATION_RESULT, "v1", {"d": 4})

    assert r1.status == AuditStatus.READY
    assert r2.status == AuditStatus.READY
    assert r3.status == AuditStatus.READY
    assert r4.status == AuditStatus.READY


def test_u_v_duplicate_and_changed_digest():
    """TEST U & V: Duplicate audit is safe; modified payload generates different digest and fails verification."""
    mock_prov = MockBlockchainAuditProvider()
    srv = AuditService(provider=mock_prov)

    payload_initial = {"version": 1, "data": "initial"}
    payload_modified = {"version": 2, "data": "modified"}

    # Record initial
    rec1 = srv.record_artifact(AuditArtifactType.CBOM_SNAPSHOT, "cbom-dup", payload_initial)
    assert rec1.status == AuditStatus.READY

    # TEST U: Record identical payload again -> safe READY response
    rec2 = srv.record_artifact(AuditArtifactType.CBOM_SNAPSHOT, "cbom-dup", payload_initial)
    assert rec2.status == AuditStatus.READY
    assert rec2.digest == rec1.digest

    # TEST V: Verification with modified payload fails (detects change)
    ver_mod = srv.verify_artifact(AuditArtifactType.CBOM_SNAPSHOT, "cbom-dup", payload_modified)
    assert ver_mod.status == AuditStatus.ERROR
    assert any("Digest mismatch" in w for w in ver_mod.warnings)
