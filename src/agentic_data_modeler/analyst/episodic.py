"""Episodic read (Phase 0) — build the prior-decision map from persisted dictionary.

Per owner decision, the agent reuses BOTH prior human-approved answers and its own
prior drafts:
  - APPROVED (a human signed off) -> reused as DECIDED (authoritative),
  - DRAFT   (the AI's own earlier guess, unverified) -> reused as a carry-forward
    INFERRED claim, clearly marked and still sent to review.
Approved always wins over a draft for the same column.

Limitation: dictionary records don't store the memory_partition, so callers scope
the input rows (same lob/domain/source, excluding the current run) before calling.
"""

from __future__ import annotations

from typing import Any


def build_prior(dictionary_attributes: list[dict[str, Any]], memory_partition: str) -> dict[str, dict[str, Any]]:
    prior: dict[str, dict[str, Any]] = {}
    for rec in dictionary_attributes:
        obj = rec.get("source_object_name")
        attr = rec.get("source_attribute_name")
        name, defn = rec.get("business_name", {}), rec.get("business_definition", {})
        if not obj or not attr or name.get("value") is None or defn.get("value") is None:
            continue                      # only reuse when both fields have a real value
        key = f"{memory_partition}::{obj}::{attr}"
        values = {"business_name": name["value"], "business_definition": defn["value"]}
        state = rec.get("lifecycle_state")
        if state == "APPROVED" and rec.get("review_decision_ref"):
            prior[key] = {"kind": "APPROVED", "review_decision_ref": rec["review_decision_ref"], "values": values}
        elif state == "DRAFT" and prior.get(key, {}).get("kind") != "APPROVED":
            prior.setdefault(key, {"kind": "DRAFT", "values": values})
    return prior
