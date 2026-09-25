import hashlib
import json
from typing import Any, Dict, Optional, Set


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


def _normalize(obj: Any, is_root: bool = True) -> Any:
    """
    Recursively normalize payload objects for deterministic JSON serialization.
    - Dict keys are converted to strings if needed.
    - Top-level 'audit' field is ignored so attached audit evidence does not alter digest.
    - Lists and tuples are normalized recursively.
    """
    if isinstance(obj, dict):
        return {
            str(k): _normalize(v, is_root=False)
            for k, v in obj.items()
            if not (is_root and str(k) == "audit")
        }
    elif isinstance(obj, (list, tuple)):
        return [_normalize(item, is_root=False) for item in obj]
    return obj


def canonicalize(payload: Any) -> bytes:
    """
    Recursively canonicalize a payload into deterministic, UTF-8 encoded compact JSON bytes.
    - Dictionary keys are sorted alphabetically.
    - Compact separators (',', ':') eliminate non-deterministic whitespace.
    - Non-finite numeric values (NaN, Infinity) are rejected with a ValueError.
    """
    normalized = _normalize(payload)
    try:
        json_str = json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (ValueError, OverflowError) as e:
        raise ValueError(f"Non-finite numeric value or non-serializable payload rejected: {e}") from e

    return json_str.encode("utf-8")


def digest_payload(payload: Any) -> str:
    """
    Compute the SHA-256 digest hex string of the canonicalized payload.
    """
    canonical_bytes = canonicalize(payload)
    return hashlib.sha256(canonical_bytes).hexdigest()
