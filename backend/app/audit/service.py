from typing import Any, Dict, Optional

from app.audit.canonicalizer import digest_payload, sanitize_metadata
from app.audit.models import AuditResult
from app.audit.provider import BlockchainAuditProvider, get_audit_provider


def _to_str(val: Any) -> str:
    if hasattr(val, "value"):
        return str(val.value)
    return str(val)


class AuditService:
    """
    Audit Service layer.
    Canonicalizes artifact payloads, computes SHA-256 digests, sanitizes metadata,
    and submits ONLY the digest and safe metadata to the audit provider.
    The raw artifact payload is NEVER passed to the provider.
    """

    def __init__(self, provider: Optional[BlockchainAuditProvider] = None):
        self.provider = provider or get_audit_provider()

    def record_artifact(
        self,
        artifact_type: Any,
        artifact_id: Any,
        payload: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditResult:
        """
        Canonicalize payload -> SHA-256 digest -> record digest with provider.
        """
        digest = digest_payload(payload)
        safe_meta = sanitize_metadata(metadata)

        return self.provider.record_artifact_digest(
            artifact_type=_to_str(artifact_type),
            artifact_id=_to_str(artifact_id),
            digest=digest,
            metadata=safe_meta,
        )

    def verify_artifact(
        self,
        artifact_type: Any,
        artifact_id: Any,
        payload: Any,
    ) -> AuditResult:
        """
        Canonicalize payload -> SHA-256 digest -> verify digest with provider.
        """
        digest = digest_payload(payload)

        return self.provider.verify_artifact_digest(
            artifact_type=_to_str(artifact_type),
            artifact_id=_to_str(artifact_id),
            digest=digest,
        )
