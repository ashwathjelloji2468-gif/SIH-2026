from typing import Any, Dict, Optional, Set

from app.audit.canonicalizer import digest_payload
from app.audit.models import AuditResult
from app.audit.provider import BlockchainAuditProvider, get_audit_provider

SENSITIVE_KEYS: Set[str] = {
    "source_code",
    "code",
    "private_key",
    "secret_key",
    "secret",
    "token",
    "auth_token",
    "password",
    "credentials",
    "raw_cbom",
    "raw_payload",
    "payload",
    "cbom",
    "raw_risk",
    "raw_recommendations",
    "migration_payload",
    "certificate_body",
    "cert_pem",
    "key_pem",
    "content",
    "file_content",
    "api_key",
}

SENSITIVE_SUBSTRINGS = (
    "private_key",
    "secret",
    "password",
    "token",
    "credential",
    "cert_pem",
    "key_pem",
)


def sanitize_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sanitizes metadata dictionary before passing to provider.
    - Strips sensitive payload keys, credentials, and source code.
    - Preserves only non-sensitive primitive metadata (e.g., version, environment, status).
    """
    if not metadata:
        return {}

    safe_meta = {}
    for k, v in metadata.items():
        k_str = str(k)
        k_lower = k_str.lower()

        if k_lower in SENSITIVE_KEYS:
            continue

        if any(sens in k_lower for sens in SENSITIVE_SUBSTRINGS):
            continue

        # Retain primitive non-sensitive metadata only
        if isinstance(v, (str, int, float, bool, type(None))):
            safe_meta[k_str] = v
        elif isinstance(v, list) and all(isinstance(item, (str, int, float, bool)) for item in v):
            safe_meta[k_str] = v

    return safe_meta


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
