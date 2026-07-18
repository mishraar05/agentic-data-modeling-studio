"""Phase 0 context assembly — fills the ``context_snapshot_id = None`` gap.

Builds the bounded context envelope for a run from the approved pack slice plus
(elsewhere) prior decisions, and persists a real, fingerprinted context_snapshot.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from . import common as C
from . import records
from .records import Scope


@dataclass(frozen=True, slots=True)
class ContextEnvelope:
    snapshot: dict[str, Any]
    module_ids: list[str]
    glossary: dict[str, str] = field(default_factory=dict)

    @property
    def snapshot_id(self) -> str:
        return self.snapshot["record_id"]


def _walk_glossary(node: Any, out: dict[str, str]) -> None:
    """Tolerant extraction: any dict with a term-ish + definition-ish pair."""
    if isinstance(node, dict):
        term = node.get("term") or node.get("name") or node.get("label")
        definition = node.get("definition") or node.get("description")
        if isinstance(term, str) and isinstance(definition, str):
            out.setdefault(term, definition)
        for value in node.values():
            _walk_glossary(value, out)
    elif isinstance(node, list):
        for item in node:
            _walk_glossary(item, out)


def _load_glossary(root: Path, manifest: dict[str, Any]) -> dict[str, str]:
    glossary: dict[str, str] = {}
    for module in manifest.get("modules", []):
        path = root / module.get("path", "")
        if path.is_file():
            try:
                _walk_glossary(yaml.safe_load(path.read_text(encoding="utf-8")), glossary)
            except yaml.YAMLError:
                continue
    return glossary


def assemble_context(root: Path, scope: Scope, *, manifest: dict[str, Any],
                     evidence_set_ref: str, evidence_fingerprint: str) -> ContextEnvelope:
    module_ids = [m["module_id"] for m in manifest.get("modules", [])]
    glossary = _load_glossary(root, manifest)
    fingerprint = C.sha256_hex(
        json.dumps({
            "pack": manifest["pack_id"], "version": manifest["pack_version"],
            "modules": sorted(module_ids), "evidence": evidence_fingerprint,
        }, sort_keys=True)
    )
    size_bytes = len(json.dumps({"modules": module_ids, "glossary": glossary}))
    snapshot = records.context_snapshot(
        root, scope, evidence_set_ref=evidence_set_ref,
        pack_id=manifest["pack_id"], pack_version=manifest["pack_version"],
        module_ids=module_ids, size_bytes=size_bytes, fingerprint=fingerprint,
    )
    return ContextEnvelope(snapshot=snapshot, module_ids=module_ids, glossary=glossary)
