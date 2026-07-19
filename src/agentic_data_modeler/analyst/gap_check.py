"""Deterministic gap & contradiction detector — the code half of Phase 5.

Guarantees (independent of any model) that these are caught and recorded as
validation_finding records:
  - COVERAGE: every observed attribute has a dictionary record;
  - CONTRADICTION: the same column name defined different ways across tables;
  - POLICY: a business name matches a governed glossary term but its definition
    diverges from that term.
The LLM critic (CR1) adds judgment on top; this pass makes the structural checks
un-missable.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from . import records as AR
from ..slice.records import Scope


def _value(claim: Any) -> str | None:
    return claim.get("value") if isinstance(claim, dict) else None


def run_gap_checks(root: str | Path, scope: Scope, *, artifact_version_ref: str,
                   dictionary_attributes: list[dict[str, Any]],
                   attribute_observations: list[dict[str, Any]],
                   dictionary_objects: list[dict[str, Any]] | None = None,
                   glossary: dict[str, str] | None = None) -> list[dict[str, Any]]:
    root = Path(root)
    glossary = glossary or {}
    findings: list[dict[str, Any]] = []

    # 1) COVERAGE — every observed attribute must have a dictionary record
    covered = {(a["source_object_name"], a["source_attribute_name"]) for a in dictionary_attributes}
    for obs in attribute_observations:
        key = (obs["object_name"], obs["attribute_name"])
        if key not in covered:
            findings.append(AR.validation_finding(
                root, scope, artifact_version_ref=artifact_version_ref,
                finding_type="COVERAGE", severity="BLOCKING",
                finding_text=f"No dictionary record for {key[0]}.{key[1]} (coverage gap)."))

    # 2) CONTRADICTION — same column name defined inconsistently across records
    by_name: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for a in dictionary_attributes:
        definition = _value(a.get("business_definition"))
        if definition:
            by_name[a["source_attribute_name"]].append((a["record_id"], definition))
    for name, entries in by_name.items():
        if len({d for _, d in entries}) > 1:
            findings.append(AR.validation_finding(
                root, scope, artifact_version_ref=artifact_version_ref,
                finding_type="CONTRADICTION", severity="WARNING",
                finding_text=f"Column '{name}' is defined {len({d for _, d in entries})} different "
                             f"ways across {len(entries)} records.",
                affected_record_refs=[rid for rid, _ in entries]))

    # 3) POLICY — business name matches a governed term but its definition diverges
    glossary_low = {t.lower(): d for t, d in glossary.items()}
    for a in dictionary_attributes:
        name, definition = _value(a.get("business_name")), _value(a.get("business_definition"))
        if name and definition and name.lower() in glossary_low:
            governed = glossary_low[name.lower()]
            if governed and governed.lower() not in definition.lower():
                findings.append(AR.validation_finding(
                    root, scope, artifact_version_ref=artifact_version_ref,
                    finding_type="POLICY", severity="INFO",
                    finding_text=f"'{name}' matches a governed term but its definition differs "
                                 f"from the glossary.",
                    affected_record_refs=[a["record_id"]]))

    return findings
