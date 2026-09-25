import hashlib
import json
from typing import Any


def _normalize(obj: Any) -> Any:
    """
    Recursively normalize payload objects for deterministic JSON serialization.
    - Dict keys are converted to strings if needed.
    - Lists and tuples are normalized recursively.
    """
    if isinstance(obj, dict):
        return {str(k): _normalize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_normalize(item) for item in obj]
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
