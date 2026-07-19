"""SA2 — map coded attribute values to governed codes from a profile distribution.

Deterministic exact-identity matching with the SA2 guardrail: a value is only
MAPPED when it matches a governed code (so the mapping can cite both a governed
code and a profile frequency); everything else is explicitly UNMAPPED. Nothing
is invented, and unknown/missing values are never merged into a real meaning.
Fuzzy/synonym matching by the model is a later enhancement layered on this.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import records as AR
from ..slice import records as R
from ..slice.records import Scope
from .confidence import derive_confidence


@dataclass(frozen=True, slots=True)
class CodeValueMapping:
    value: str
    frequency: int
    state: str                      # MAPPED | UNMAPPED
    governed_code: str | None = None


def map_code_values(distribution: dict[str, int], code_set: dict[str, str]) -> list[CodeValueMapping]:
    """distribution: observed value -> frequency; code_set: governed_code -> meaning."""
    out: list[CodeValueMapping] = []
    for value, freq in distribution.items():
        matched = value if value in code_set else None
        out.append(CodeValueMapping(
            value=value, frequency=int(freq),
            state="MAPPED" if matched else "UNMAPPED", governed_code=matched))
    return out


def code_value_records(root: str | Path, scope: Scope, *, context_snapshot_ref: str,
                       attribute_ref: str, evidence_item_ref: str,
                       distribution: dict[str, int],
                       code_set: dict[str, dict[str, Any]]) -> tuple[list[dict], list[str]]:
    """Persist MAPPED values as code_value records (cite governed code + profile freq).

    code_set: observed_code -> {"meaning": str, "governed_code_ref": {...}}. A value is
    only MAPPED when a governed code identity exists; everything else is returned as
    UNMAPPED (the caller raises one open_question, never a fabricated meaning).
    """
    records: list[dict] = []
    unmapped: list[str] = []
    for code, freq in distribution.items():
        entry = code_set.get(code)
        if entry and entry.get("governed_code_ref"):
            conf = derive_confidence(evidence_refs=[evidence_item_ref], is_glossary_hit=True)
            meaning = R.inferred_claim(entry["meaning"], "TEXT", [evidence_item_ref], conf)
            records.append(AR.code_value(
                root, scope, context_snapshot_ref=context_snapshot_ref, attribute_ref=attribute_ref,
                evidence_item_ref=evidence_item_ref, code=code, meaning=meaning,
                frequency=int(freq), governed_code_ref=entry["governed_code_ref"]))
        else:
            unmapped.append(code)
    return records, unmapped
