"""Episodic memory service (ADR-006) — the read/write loop over the decision ledger.

This is the durable decision-memory projection used by later context snapshots: it
persists review decisions and open questions (the ledger) and answers the one
question Phase 0 needs — "has a human already decided X about this attribute?".
JSON-backed here; swap for the Delta ``review_decision`` / ``open_question``
tables without changing callers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def subject_key(memory_partition: str, object_name: str, attribute_name: str) -> str:
    return f"{memory_partition}::{object_name}::{attribute_name}"


class EpisodicMemory:
    def __init__(self, store_path: Path):
        self.path = Path(store_path)
        self._data: dict[str, Any] = {"decisions": [], "open_questions": []}
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    # --- write path (Phase 8) ---
    def write_decision(self, key: str, decision_record: dict[str, Any],
                       payload: dict[str, Any] | None = None) -> None:
        self._data["decisions"].append(
            {"subject_key": key, "record": decision_record, "payload": payload or {}}
        )
        self._flush()

    def write_open_question(self, key: str, question_record: dict[str, Any]) -> None:
        self._data["open_questions"].append({"subject_key": key, "record": question_record})
        self._flush()

    # --- read path (Phase 0 read-back) ---
    def prior_decision(self, key: str) -> dict[str, Any] | None:
        """Latest APPROVE decision entry ({record, payload}) for this subject, or None."""
        for entry in reversed(self._data["decisions"]):
            if entry["subject_key"] == key and entry["record"].get("decision") == "APPROVE":
                return entry
        return None

    def all_decisions(self) -> list[dict[str, Any]]:
        return [e["record"] for e in self._data["decisions"]]

    def all_open_questions(self) -> list[dict[str, Any]]:
        return [e["record"] for e in self._data["open_questions"]]
