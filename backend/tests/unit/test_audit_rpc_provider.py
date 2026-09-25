import os
import pytest
from app.audit import (
    AuditArtifactType,
    AuditResult,
    AuditService,
    AuditStatus,
    BlockchainRPCAuditProvider,
    MockBlockchainAuditProvider,
    UnconfiguredBlockchainAuditProvider,
    digest_payload,
    get_audit_provider,
)
from app.audit.integration import audit_cbom_snapshot, audit_recommendation_snapshot


def test_a_missing_provider_configuration(monkeypatch):
    """TEST A: Missing provider configuration -> UNCONFIGURED."""
    monkeypatch.delenv("SENTRIQ_BLOCKCHAIN_PROVIDER", raising=False)
    provider = get_audit_provider()
    assert isinstance(provider, UnconfiguredBlockchainAuditProvider)

    res = provider.record_artifact_digest("cbom_snapshot", "cbom-1", "digest123")
    assert res.status == AuditStatus.UNCONFIGURED
    assert any("not configured" in w for w in res.warnings)


def test_b_incomplete_real_provider_configuration():
    """TEST B: Incomplete real-provider configuration -> UNCONFIGURED."""
    # Missing rpc_url or contract_address
    provider = BlockchainRPCAuditProvider(rpc_url=None, contract_address=None)
    assert not provider.is_configured

    res = provider.record_artifact_digest("cbom_snapshot", "cbom-1", "digest123")
    assert res.status == AuditStatus.UNCONFIGURED
    assert any("unconfigured" in w for w in res.warnings)


def test_c_unsupported_provider_name(monkeypatch):
    """TEST C: Unsupported provider name -> UNCONFIGURED."""
    monkeypatch.setenv("SENTRIQ_BLOCKCHAIN_PROVIDER", "invalid_provider_name")
    provider = get_audit_provider()
    assert isinstance(provider, UnconfiguredBlockchainAuditProvider)

    res = provider.record_artifact_digest("cbom_snapshot", "cbom-1", "digest123")
    assert res.status == AuditStatus.UNCONFIGURED
    assert any("Unsupported" in w for w in res.warnings)


def test_d_e_rpc_provider_digest_operation():
    """TEST D & E: Real provider constructs digest operation and receives digest, never raw artifact payload."""
    rpc_prov = BlockchainRPCAuditProvider(
        rpc_url="mock://rpc.sentriq.local",
        contract_address="0x1234567890abcdef1234567890abcdef12345678",
        network="sepolia",
    )
    service = AuditService(provider=rpc_prov)

    raw_payload = {
        "sensitive_code": "def secret_code(): pass",
        "private_key": "SUPER_SECRET_KEY",
        "components": [{"name": "ML-KEM-768"}],
    }

    res = service.record_artifact(
        artifact_type=AuditArtifactType.CBOM_SNAPSHOT,
        artifact_id="cbom-rpc-1",
        payload=raw_payload,
    )

    assert res.status == AuditStatus.READY
    assert res.digest == digest_payload(raw_payload)
    assert res.transaction_id is not None
    assert res.transaction_id.startswith("0x")
    assert res.network == "sepolia"


def test_f_successful_transaction_hash():
    """TEST F: Successful mocked transaction -> READY with actual non-null transaction hash."""
    rpc_prov = BlockchainRPCAuditProvider(
        rpc_url="mock://rpc.sentriq.local",
        contract_address="0xContractAddress",
        network="ethereum-mainnet",
    )

    res = rpc_prov.record_artifact_digest("cbom_snapshot", "cbom-tx-test", "a1b2c3d4e5f6")

    assert res.status == AuditStatus.READY
    assert res.transaction_id is not None
    assert res.transaction_id.startswith("0x")
    assert res.network == "ethereum-mainnet"


def test_g_no_transaction_hash_returns_error(monkeypatch):
    """TEST G: No transaction hash returned -> ERROR, never fabricated READY."""
    rpc_prov = BlockchainRPCAuditProvider(
        rpc_url="mock://rpc.sentriq.local",
        contract_address="0xContractAddress",
    )
    monkeypatch.setattr(rpc_prov, "_submit_rpc_transaction", lambda *args, **kwargs: None)

    res = rpc_prov.record_artifact_digest("cbom_snapshot", "cbom-no-hash", "a1b2c3d4e5f6")

    assert res.status == AuditStatus.ERROR
    assert res.transaction_id is None
    assert any("failed to return" in w for w in res.warnings)


def test_h_i_j_verification_semantics():
    """TEST H, I, J: Verification MATCH, MISMATCH, and NOT FOUND."""
    rpc_prov = BlockchainRPCAuditProvider(
        rpc_url="mock://rpc.sentriq.local",
        contract_address="0xContractAddress",
    )

    digest_orig = "1111111111111111111111111111111111111111111111111111111111111111"
    digest_diff = "2222222222222222222222222222222222222222222222222222222222222222"

    rpc_prov.record_artifact_digest("cbom_snapshot", "cbom-v1", digest_orig)

    # TEST H: Verification MATCH
    v_match = rpc_prov.verify_artifact_digest("cbom_snapshot", "cbom-v1", digest_orig)
    assert v_match.status == AuditStatus.READY
    assert any("match confirmed" in e for e in v_match.evidence)

    # TEST I: Verification MISMATCH
    v_mismatch = rpc_prov.verify_artifact_digest("cbom_snapshot", "cbom-v1", digest_diff)
    assert v_mismatch.status == AuditStatus.ERROR
    assert any("mismatch" in w for w in v_mismatch.warnings)

    # TEST J: Verification NOT FOUND
    v_notfound = rpc_prov.verify_artifact_digest("cbom_snapshot", "cbom-unknown", digest_orig)
    assert v_notfound.status == AuditStatus.ERROR
    assert any("not found" in w for w in v_notfound.warnings)


def test_k_l_rpc_and_contract_error_handling(monkeypatch):
    """TEST K & L: RPC / contract failure returns ERROR without crashing."""
    rpc_prov = BlockchainRPCAuditProvider(
        rpc_url="mock://rpc.sentriq.local",
        contract_address="0xContractAddress",
    )

    def raise_rpc_err(*args, **kwargs):
        raise RuntimeError("RPC Connection Refused (503)")

    monkeypatch.setattr(rpc_prov, "_submit_rpc_transaction", raise_rpc_err)

    res = rpc_prov.record_artifact_digest("cbom_snapshot", "cbom-err", "digest123")

    assert res.status == AuditStatus.ERROR
    assert any("RPC Connection Refused" in w for w in res.warnings)


def test_m_n_idempotency_and_changed_digest_detection():
    """TEST M & N: Idempotent recording & changed digest detection."""
    rpc_prov = BlockchainRPCAuditProvider(
        rpc_url="mock://rpc.sentriq.local",
        contract_address="0xContractAddress",
    )

    digest1 = "3333333333333333333333333333333333333333333333333333333333333333"
    digest2 = "4444444444444444444444444444444444444444444444444444444444444444"

    res1 = rpc_prov.record_artifact_digest("recommendation_snapshot", "rec-idem", digest1)
    res2 = rpc_prov.record_artifact_digest("recommendation_snapshot", "rec-idem", digest1)

    # TEST M: Idempotent return
    assert res1.status == AuditStatus.READY
    assert res2.status == AuditStatus.READY
    assert res1.transaction_id == res2.transaction_id

    # TEST N: Changed digest remains detectable
    ver_mod = rpc_prov.verify_artifact_digest("recommendation_snapshot", "rec-idem", digest2)
    assert ver_mod.status == AuditStatus.ERROR
    assert any("mismatch" in w for w in ver_mod.warnings)


def test_o_sensitive_metadata_excluded_from_blockchain_call():
    """TEST O: Sensitive metadata is excluded from blockchain call payload."""
    rpc_prov = BlockchainRPCAuditProvider(
        rpc_url="mock://rpc.sentriq.local",
        contract_address="0xContractAddress",
    )

    metadata = {
        "version": "1.0",
        "private_key": "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoI...",
        "source_code": "secret_function()",
        "environment": "production",
    }

    res = rpc_prov.record_artifact_digest("cbom_snapshot", "cbom-meta-sec", "digest123", metadata=metadata)

    assert res.status == AuditStatus.READY
    stored_meta = rpc_prov._mock_rpc_ledger[("cbom_snapshot", "cbom-meta-sec")]["metadata"]
    assert "private_key" not in stored_meta
    assert "source_code" not in stored_meta
    assert stored_meta.get("version") == "1.0"
    assert stored_meta.get("environment") == "production"


def test_p_core_sentriq_flow_non_blocking_on_blockchain_failure(monkeypatch):
    """TEST P: Core SENTRIQ flow remains successful when blockchain provider fails."""
    err_prov = BlockchainRPCAuditProvider(
        rpc_url="mock://rpc.sentriq.local",
        contract_address="0xContractAddress",
    )
    monkeypatch.setattr(err_prov, "_submit_rpc_transaction", lambda *args, **kwargs: 1 / 0)

    srv = AuditService(provider=err_prov)

    # Calling audit_cbom_snapshot with failing RPC provider
    res = audit_cbom_snapshot({"bomFormat": "CycloneDX"}, scan_id="s-fail", service=srv)

    assert res is not None
    assert res.status == AuditStatus.ERROR
    assert any("division by zero" in w or "error" in w.lower() for w in res.warnings)


def test_q_mock_provider_remains_functional():
    """TEST Q: Mock provider remains fully functional."""
    mock_prov = MockBlockchainAuditProvider(network="test-net")
    srv = AuditService(provider=mock_prov)

    res = srv.record_artifact(AuditArtifactType.CBOM_SNAPSHOT, "c-mock", {"test": 1})
    assert res.status == AuditStatus.READY
    assert res.provider_name == "MockBlockchainAuditProvider"

    ver = srv.verify_artifact(AuditArtifactType.CBOM_SNAPSHOT, "c-mock", {"test": 1})
    assert ver.status == AuditStatus.READY


def test_r_provider_selection(monkeypatch):
    """TEST R: Provider selection correctly chooses mock vs real provider."""
    # Test mock selection
    monkeypatch.setenv("SENTRIQ_BLOCKCHAIN_PROVIDER", "mock")
    prov_mock = get_audit_provider()
    assert isinstance(prov_mock, MockBlockchainAuditProvider)

    # Test blockchain selection with missing config -> Unconfigured
    monkeypatch.setenv("SENTRIQ_BLOCKCHAIN_PROVIDER", "blockchain")
    monkeypatch.delenv("SENTRIQ_BLOCKCHAIN_RPC_URL", raising=False)
    prov_unconfig = get_audit_provider()
    assert isinstance(prov_unconfig, UnconfiguredBlockchainAuditProvider)

    # Test blockchain selection with complete config -> BlockchainRPCAuditProvider
    monkeypatch.setenv("SENTRIQ_BLOCKCHAIN_RPC_URL", "mock://rpc.sentriq.local")
    monkeypatch.setenv("SENTRIQ_BLOCKCHAIN_CONTRACT_ADDRESS", "0xContractAddress")
    prov_rpc = get_audit_provider()
    assert isinstance(prov_rpc, BlockchainRPCAuditProvider)


def test_s_t_no_secrets_in_logs_and_truthful_attribution():
    """TEST S & T: No secret values appear in audit evidence, and no fake network/tx/timestamp reported."""
    rpc_prov = BlockchainRPCAuditProvider(
        rpc_url="mock://rpc.sentriq.local",
        contract_address="0xContractAddress",
        network="sepolia",
        private_key="SECRET_KEY_DO_NOT_EXPOSE",
    )

    res = rpc_prov.record_artifact_digest("cbom_snapshot", "cbom-secret-check", "digest123")

    assert res.status == AuditStatus.READY
    assert res.network == "sepolia"
    assert "SECRET_KEY" not in str(res.model_dump())
    assert "SECRET_KEY" not in "".join(res.evidence)
