import datetime
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.audit.models import AuditResult, AuditStatus


class BlockchainAuditProvider(ABC):
    """
    Abstract Base Class for Audit Providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def record_artifact_digest(
        self,
        artifact_type: str,
        artifact_id: str,
        digest: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditResult:
        pass

    @abstractmethod
    def verify_artifact_digest(
        self,
        artifact_type: str,
        artifact_id: str,
        digest: str,
    ) -> AuditResult:
        pass


class MockBlockchainAuditProvider(BlockchainAuditProvider):
    """
    In-memory mock audit provider for local development, unit tests, and CI.
    Stores digest records strictly in memory. Never fabricates blockchain transaction IDs.
    """

    def __init__(self, network: str = "in-memory-mock"):
        self.network_name = network
        self._records: Dict[tuple[str, str], Dict[str, Any]] = {}

    @property
    def provider_name(self) -> str:
        return "MockBlockchainAuditProvider"

    def record_artifact_digest(
        self,
        artifact_type: str,
        artifact_id: str,
        digest: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditResult:
        key = (artifact_type, artifact_id)
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        self._records[key] = {
            "digest": digest,
            "metadata": metadata or {},
            "timestamp": now_iso,
        }

        return AuditResult(
            status=AuditStatus.READY,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            digest=digest,
            transaction_id=None,  # Truthful: null for mock/in-memory provider
            network=self.network_name,
            provider_name=self.provider_name,
            timestamp=now_iso,
            evidence=[
                f"Digest {digest[:16]}... recorded in-memory for {artifact_type}:{artifact_id}."
            ],
            warnings=[],
        )

    def verify_artifact_digest(
        self,
        artifact_type: str,
        artifact_id: str,
        digest: str,
    ) -> AuditResult:
        key = (artifact_type, artifact_id)
        record = self._records.get(key)
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if not record:
            return AuditResult(
                status=AuditStatus.ERROR,
                artifact_type=artifact_type,
                artifact_id=artifact_id,
                digest=digest,
                transaction_id=None,
                network=self.network_name,
                provider_name=self.provider_name,
                timestamp=now_iso,
                evidence=[],
                warnings=[f"Artifact {artifact_type}:{artifact_id} not found in audit ledger."],
            )

        recorded_digest = record["digest"]
        if recorded_digest == digest:
            return AuditResult(
                status=AuditStatus.READY,
                artifact_type=artifact_type,
                artifact_id=artifact_id,
                digest=digest,
                transaction_id=None,
                network=self.network_name,
                provider_name=self.provider_name,
                timestamp=record.get("timestamp", now_iso),
                evidence=[f"Digest match confirmed for {artifact_type}:{artifact_id}."],
                warnings=[],
            )
        else:
            return AuditResult(
                status=AuditStatus.ERROR,
                artifact_type=artifact_type,
                artifact_id=artifact_id,
                digest=digest,
                transaction_id=None,
                network=self.network_name,
                provider_name=self.provider_name,
                timestamp=now_iso,
                evidence=[],
                warnings=[
                    f"Digest mismatch for {artifact_type}:{artifact_id}. Recorded: {recorded_digest}, Provided: {digest}."
                ],
            )


class UnconfiguredBlockchainAuditProvider(BlockchainAuditProvider):
    """
    Audit provider representing absent or incomplete configuration.
    Returns status = UNCONFIGURED with truthful warnings.
    """

    def __init__(self, reason: str = "Blockchain audit provider is not configured."):
        self.reason = reason

    @property
    def provider_name(self) -> str:
        return "UnconfiguredBlockchainAuditProvider"

    def record_artifact_digest(
        self,
        artifact_type: str,
        artifact_id: str,
        digest: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditResult:
        return AuditResult(
            status=AuditStatus.UNCONFIGURED,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            digest=digest,
            transaction_id=None,
            network=None,
            provider_name=self.provider_name,
            timestamp=None,
            evidence=[],
            warnings=[self.reason],
        )

    def verify_artifact_digest(
        self,
        artifact_type: str,
        artifact_id: str,
        digest: str,
    ) -> AuditResult:
        return AuditResult(
            status=AuditStatus.UNCONFIGURED,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            digest=digest,
            transaction_id=None,
            network=None,
            provider_name=self.provider_name,
            timestamp=None,
            evidence=[],
            warnings=[self.reason],
        )


class ErrorBlockchainAuditProvider(BlockchainAuditProvider):
    """
    Audit provider representing an operational failure.
    Returns status = ERROR without fabricating successful evidence.
    """

    def __init__(self, error_message: str = "Blockchain provider error encountered."):
        self.error_message = error_message

    @property
    def provider_name(self) -> str:
        return "ErrorBlockchainAuditProvider"

    def record_artifact_digest(
        self,
        artifact_type: str,
        artifact_id: str,
        digest: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditResult:
        return AuditResult(
            status=AuditStatus.ERROR,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            digest=digest,
            transaction_id=None,
            network=None,
            provider_name=self.provider_name,
            timestamp=None,
            evidence=[],
            warnings=[self.error_message],
        )

    def verify_artifact_digest(
        self,
        artifact_type: str,
        artifact_id: str,
        digest: str,
    ) -> AuditResult:
        return AuditResult(
            status=AuditStatus.ERROR,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            digest=digest,
            transaction_id=None,
            network=None,
            provider_name=self.provider_name,
            timestamp=None,
            evidence=[],
            warnings=[self.error_message],
        )


def get_audit_provider(
    provider_type: Optional[str] = None,
    network: Optional[str] = None,
) -> BlockchainAuditProvider:
    """
    Factory function to resolve the active BlockchainAuditProvider from environment variables:
    - SENTRIQ_BLOCKCHAIN_PROVIDER ('mock' | 'in_memory' | 'unconfigured' | ...)
    - SENTRIQ_BLOCKCHAIN_NETWORK
    - SENTRIQ_BLOCKCHAIN_RPC_URL
    - SENTRIQ_BLOCKCHAIN_CONTRACT_ADDRESS
    """
    p_type = provider_type if provider_type is not None else os.getenv("SENTRIQ_BLOCKCHAIN_PROVIDER")
    net = network if network is not None else os.getenv("SENTRIQ_BLOCKCHAIN_NETWORK") or "in-memory-mock"

    if not p_type:
        return UnconfiguredBlockchainAuditProvider(
            "SENTRIQ_BLOCKCHAIN_PROVIDER environment variable is not configured."
        )

    normalized = str(p_type).lower().strip()
    if normalized in ("mock", "in_memory", "in-memory", "test"):
        return MockBlockchainAuditProvider(network=net)
    elif normalized in ("unconfigured", "disabled", "none", "off", ""):
        return UnconfiguredBlockchainAuditProvider(
            "Blockchain audit provider is explicitly configured as unconfigured/disabled."
        )
    else:
        return UnconfiguredBlockchainAuditProvider(
            f"Unsupported or unrecognized blockchain audit provider: '{p_type}'"
        )
