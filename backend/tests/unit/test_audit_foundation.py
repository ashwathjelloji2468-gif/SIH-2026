import math
import os
import sqlite3
import pytest
from typing import Any, Dict, Optional

from app.audit import (
    AuditArtifactType,
    AuditResult,
    AuditService,
    AuditStatus,
    BlockchainAuditProvider,
    ErrorBlockchainAuditProvider,
    MockBlockchainAuditProvider,
    UnconfiguredBlockchainAuditProvider,
    canonicalize,
    digest_payload,
    get_audit_provider,
    sanitize_metadata,
)


class SpyAuditProvider(BlockchainAuditProvider):
    """
    Spy provider to record exact parameters passed to record_artifact_digest and verify_artifact_digest.
    """

    def __init__(self):
        self.recorded_calls = []
        self.verified_calls = []

    @property
    def provider_name(self) -> str:
        return "SpyAuditProvider"

    def record_artifact_digest(
        self,
        artifact_type: str,
        artifact_id: str,
        digest: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditResult:
        self.recorded_calls.append({
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
            transaction_id=None,
            network="spy",
            provider_name=self.provider_name,
            evidence=["Spy recorded digest."],
        )

    def verify_artifact_digest(
        self,
        artifact_type: str,
        artifact_id: str,
        digest: str,
    ) -> AuditResult:
        self.verified_calls.append({
            "artifact_type": artifact_type,
            "artifact_id": artifact_id,
            "digest": digest,
        })
        return AuditResult(
            status=AuditStatus.READY,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            digest=digest,
            transaction_id=None,
            network="spy",
            provider_name=self.provider_name,
            evidence=["Spy verified digest."],
        )


def test_a_dict_insertion_order_invariance():
    """TEST A: Same payload + different dictionary insertion order => identical canonical bytes and SHA-256 digest."""
    payload1 = {"b": 2, "a": 1, "z": {"y": "hello", "x": [3, 2, 1]}}
    payload2 = {"z": {"x": [3, 2, 1], "y": "hello"}, "a": 1, "b": 2}

    bytes1 = canonicalize(payload1)
    bytes2 = canonicalize(payload2)
    digest1 = digest_payload(payload1)
    digest2 = digest_payload(payload2)

    assert bytes1 == bytes2
    assert digest1 == digest2


def test_b_meaningfully_different_payloads():
    """TEST B: Meaningfully different payload => different digest."""
    payload1 = {"algorithm": "RSA-2048", "safety": "VULNERABLE"}
    payload2 = {"algorithm": "ML-KEM-768", "safety": "SAFE"}

    digest1 = digest_payload(payload1)
    digest2 = digest_payload(payload2)

    assert digest1 != digest2


def test_c_nested_structures_canonicalization():
    """TEST C: Nested dictionaries/lists canonicalize deterministically."""
    nested = {
        "outer": {
            "inner_b": [{"k2": "v2", "k1": "v1"}],
            "inner_a": 100,
        },
        "list": [3, 1, 2],
    }
    canonical_bytes = canonicalize(nested)
    expected_bytes = b'{"list":[3,1,2],"outer":{"inner_a":100,"inner_b":[{"k1":"v1","k2":"v2"}]}}'
    assert canonical_bytes == expected_bytes


def test_d_reject_non_finite_numerics():
    """TEST D: Non-finite numeric values (NaN, Infinity) are rejected."""
    payload_nan = {"val": float("nan")}
    payload_inf = {"val": float("inf")}
    payload_neginf = {"val": float("-inf")}

    with pytest.raises(ValueError, match="Non-finite"):
        canonicalize(payload_nan)

    with pytest.raises(ValueError, match="Non-finite"):
        canonicalize(payload_inf)

    with pytest.raises(ValueError, match="Non-finite"):
        canonicalize(payload_neginf)


def test_e_mock_provider_record():
    """TEST E: Mock provider can record a digest successfully."""
    provider = MockBlockchainAuditProvider(network="test-net")
    service = AuditService(provider=provider)

    payload = {"cbom": "sample cbom content", "version": "1.0"}
    res = service.record_artifact(
        artifact_type=AuditArtifactType.CBOM_SNAPSHOT,
        artifact_id="cbom-001",
        payload=payload,
        metadata={"environment": "test"},
    )

    assert res.status == AuditStatus.READY
    assert res.artifact_type == "cbom_snapshot"
    assert res.artifact_id == "cbom-001"
    assert res.digest == digest_payload(payload)
    assert res.provider_name == "MockBlockchainAuditProvider"
    assert res.network == "test-net"


def test_f_mock_provider_verify_success():
    """TEST F: Mock provider can verify a previously recorded digest."""
    provider = MockBlockchainAuditProvider()
    service = AuditService(provider=provider)

    payload = {"risk_score": 85.5, "threat": "High"}
    service.record_artifact(
        artifact_type=AuditArtifactType.RISK_ASSESSMENT_SNAPSHOT,
        artifact_id="risk-001",
        payload=payload,
    )

    verify_res = service.verify_artifact(
        artifact_type=AuditArtifactType.RISK_ASSESSMENT_SNAPSHOT,
        artifact_id="risk-001",
        payload=payload,
    )

    assert verify_res.status == AuditStatus.READY
    assert len(verify_res.evidence) > 0
    assert len(verify_res.warnings) == 0


def test_g_modified_digest_fails_verification():
    """TEST G: Modified digest for the same artifact fails verification."""
    provider = MockBlockchainAuditProvider()
    service = AuditService(provider=provider)

    original_payload = {"pqc_candidate": "ML-KEM-768"}
    modified_payload = {"pqc_candidate": "ML-KEM-1024"}

    service.record_artifact(
        artifact_type=AuditArtifactType.RECOMMENDATION_SNAPSHOT,
        artifact_id="rec-001",
        payload=original_payload,
    )

    verify_res = service.verify_artifact(
        artifact_type=AuditArtifactType.RECOMMENDATION_SNAPSHOT,
        artifact_id="rec-001",
        payload=modified_payload,
    )

    assert verify_res.status == AuditStatus.ERROR
    assert any("Digest mismatch" in w for w in verify_res.warnings)


def test_h_unknown_artifact_verification():
    """TEST H: Unknown artifact verification is handled truthfully."""
    provider = MockBlockchainAuditProvider()
    service = AuditService(provider=provider)

    verify_res = service.verify_artifact(
        artifact_type=AuditArtifactType.MIGRATION_VALIDATION_RESULT,
        artifact_id="non-existent-id",
        payload={"status": "PASS"},
    )

    assert verify_res.status == AuditStatus.ERROR
    assert any("not found" in w for w in verify_res.warnings)


def test_i_no_fabricated_transaction_id():
    """TEST I: No transaction ID is fabricated."""
    provider = MockBlockchainAuditProvider()
    service = AuditService(provider=provider)

    res = service.record_artifact(
        artifact_type=AuditArtifactType.CBOM_SNAPSHOT,
        artifact_id="cbom-002",
        payload={"data": "test"},
    )

    assert res.transaction_id is None


def test_j_provider_never_receives_raw_payload():
    """TEST J: Provider receives digest, never the raw artifact payload."""
    spy_provider = SpyAuditProvider()
    service = AuditService(provider=spy_provider)

    raw_payload = {
        "sensitive_code": "def secret_algorithm(): return 42",
        "secret_key": "SUPER_SECRET_PRIVATE_KEY",
        "nested": {"deep": "secret"},
    }

    service.record_artifact(
        artifact_type=AuditArtifactType.CBOM_SNAPSHOT,
        artifact_id="cbom-raw-test",
        payload=raw_payload,
    )

    assert len(spy_provider.recorded_calls) == 1
    call = spy_provider.recorded_calls[0]

    # Verify digest is present
    assert call["digest"] == digest_payload(raw_payload)

    # Verify raw payload structure was not passed to provider
    assert "raw_payload" not in call
    assert "payload" not in call
    assert call["digest"] != str(raw_payload)


def test_k_sensitive_payload_fields_excluded_from_metadata():
    """TEST K: Sensitive payload fields are not passed to the provider in metadata."""
    metadata = {
        "environment": "production",
        "version": "v1.2.3",
        "source_code": "import ssl; ssl.secret()",
        "private_key": "-----BEGIN PRIVATE KEY-----",
        "secret_key": "mysecret",
        "credentials": "admin:password",
    }

    sanitized = sanitize_metadata(metadata)

    assert "environment" in sanitized
    assert "version" in sanitized
    assert "source_code" not in sanitized
    assert "private_key" not in sanitized
    assert "secret_key" not in sanitized
    assert "credentials" not in sanitized


def test_l_unconfigured_provider_handling(monkeypatch):
    """TEST L: Missing/unconfigured provider returns status = UNCONFIGURED with truthful warning."""
    monkeypatch.delenv("SENTRIQ_BLOCKCHAIN_PROVIDER", raising=False)
    provider = get_audit_provider()
    service = AuditService(provider=provider)

    res = service.record_artifact(
        artifact_type=AuditArtifactType.CBOM_SNAPSHOT,
        artifact_id="cbom-unconfig",
        payload={"test": 1},
    )

    assert res.status == AuditStatus.UNCONFIGURED
    assert res.provider_name == "UnconfiguredBlockchainAuditProvider"
    assert any("not configured" in w for w in res.warnings)


def test_m_provider_error_surfaced():
    """TEST M: Provider error is surfaced as status = ERROR without fabricating successful evidence."""
    error_provider = ErrorBlockchainAuditProvider(error_message="Blockchain node connection timed out")
    service = AuditService(provider=error_provider)

    res = service.record_artifact(
        artifact_type=AuditArtifactType.RISK_ASSESSMENT_SNAPSHOT,
        artifact_id="risk-err",
        payload={"risk": "high"},
    )

    assert res.status == AuditStatus.ERROR
    assert res.transaction_id is None
    assert len(res.evidence) == 0
    assert "Blockchain node connection timed out" in res.warnings[0]


def test_n_all_four_artifact_types_accepted():
    """TEST N: All four planned artifact types are accepted by the abstraction."""
    provider = MockBlockchainAuditProvider()
    service = AuditService(provider=provider)

    artifact_types = [
        AuditArtifactType.CBOM_SNAPSHOT,
        AuditArtifactType.RISK_ASSESSMENT_SNAPSHOT,
        AuditArtifactType.RECOMMENDATION_SNAPSHOT,
        AuditArtifactType.MIGRATION_VALIDATION_RESULT,
    ]

    for atype in artifact_types:
        res = service.record_artifact(
            artifact_type=atype,
            artifact_id=f"id-{atype.value}",
            payload={"type": atype.value},
        )
        assert res.status == AuditStatus.READY
        assert res.artifact_type == atype.value


def test_o_existing_application_imports_unaffected():
    """TEST O: Existing SENTRIQ application imports remain unaffected."""
    # Verify core application components import without side effects or errors
    from app.main import app
    from app.models.db_models import Project, Scan
    from app.recommend.service import RecommendationService
    from app.recommend.performance_provider import PerformancePredictionProvider
    from app.services.business_criticality_service import BusinessCriticalityService

    assert app is not None
    assert Project is not None
    assert Scan is not None
    assert RecommendationService is not None
    assert PerformancePredictionProvider is not None
    assert BusinessCriticalityService is not None


def test_p_audit_foundation_does_not_modify_database_schema():
    """TEST P: Audit foundation does not modify database schema."""
    db_path = "ecdat.db"
    if not os.path.exists(db_path):
        pytest.skip("ecdat.db path not found")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query all tables in the SQLite database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}

    conn.close()

    # Ensure no new tamper-evident audit tables were created in the database schema
    assert "blockchain_audit_records" not in tables
    assert "tamper_evident_logs" not in tables
