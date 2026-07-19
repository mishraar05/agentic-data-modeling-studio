"""Shared helpers: stable IDs, timestamps, envelopes, fingerprints."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "0.1.0"

# Contract $ids emitted by the slice.
C_CONTEXT_SNAPSHOT = "urn:agentic-data-modeler:contract:context_snapshot:0.1.0"
C_OBJECT_OBS = "urn:agentic-data-modeler:contract:source_object_observation:0.1.0"
C_ATTRIBUTE_OBS = "urn:agentic-data-modeler:contract:source_attribute_observation:0.1.0"
C_DICT_ATTR = "urn:agentic-data-modeler:contract:source_dictionary_attribute:0.1.0"
C_OPEN_QUESTION = "urn:agentic-data-modeler:contract:open_question:0.1.0"
C_REVIEW_ITEM = "urn:agentic-data-modeler:contract:review_item:0.1.0"
C_REVIEW_DECISION = "urn:agentic-data-modeler:contract:review_decision:0.1.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def stable_id(prefix: str, *parts: str) -> str:
    """Deterministic id that does not leak physical names into the identifier."""
    content = json.dumps(parts, ensure_ascii=True, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(content.encode('utf-8')).hexdigest()[:32]}"


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def envelope(
    *,
    record_id: str,
    lob: str,
    domain: str,
    artifact_version: str,
    lifecycle_state: str,
    provenance: dict[str, Any],
    created_at: str | None = None,
    schema_version: str = SCHEMA_VERSION,
) -> dict[str, Any]:
    """Build the shared contract envelope (see contracts/_common.schema.json)."""
    ts = created_at or now_iso()
    return {
        "record_id": record_id,
        "schema_version": schema_version,
        "lob": lob,
        "domain": domain,
        "artifact_version": artifact_version,
        "lifecycle_state": lifecycle_state,
        "provenance": provenance,
        "created_at": ts,
        "updated_at": ts,
    }
