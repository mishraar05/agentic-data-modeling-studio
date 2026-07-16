"""Fail-closed selection of approved knowledge packs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .validation import KnowledgeValidationError, load_yaml, resolve_inside, validate_repository_pack


class KnowledgeSelectionError(ValueError):
    """Raised when a requested pack is absent, unauthorized, or out of scope."""


def _scope_matches(scope: dict[str, Any], geography: str, lob: str, domains: set[str]) -> bool:
    return (
        scope.get("geography") == geography
        and scope.get("lob") == lob
        and domains.issubset(set(scope.get("domains", [])))
    )


def select_approved_pack(
    repository_root: Path,
    *,
    pack_id: str,
    pack_version: str,
    geography: str,
    lob: str,
    domains: set[str],
) -> dict[str, Any]:
    """Return an exact approved pack or fail without fallback."""

    root = repository_root.resolve()
    registry = load_yaml(root / "knowledge/registry/pack_registry.yml")
    matches = [
        item
        for item in registry.get("packs", [])
        if item.get("pack_id") == pack_id and str(item.get("pack_version")) == pack_version
    ]
    if len(matches) != 1:
        raise KnowledgeSelectionError("Exactly one registered pack version is required")
    record = matches[0]
    if record.get("approval_state") != "APPROVED" or record.get("runtime_eligible") is not True:
        raise KnowledgeSelectionError("Registry does not authorize this pack for runtime use")

    try:
        manifest_path = resolve_inside(root, record["manifest"])
        manifest_relative = manifest_path.relative_to(root).as_posix()
        manifest = validate_repository_pack(root, manifest_relative)
    except (KeyError, KnowledgeValidationError) as exc:
        raise KnowledgeSelectionError(str(exc)) from exc

    if manifest["pack_id"] != pack_id or manifest["pack_version"] != pack_version:
        raise KnowledgeSelectionError("Registry and manifest identities do not match")
    if manifest["approval_state"] != "APPROVED" or manifest["runtime_eligible"] is not True:
        raise KnowledgeSelectionError("Manifest does not authorize this pack for runtime use")
    if not _scope_matches(manifest["scope"], geography, lob, domains):
        raise KnowledgeSelectionError("Requested scope is not covered by the approved pack")

    return manifest

