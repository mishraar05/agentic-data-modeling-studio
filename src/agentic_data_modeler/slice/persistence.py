"""Local record store standing in for the authoritative Delta tables (Phase 9)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


class RecordStore:
    def __init__(self, store_path: Path):
        self.path = Path(store_path)
        self._data: dict[str, list[dict]] = defaultdict(list)
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._data = defaultdict(list, {k: list(v) for k, v in raw.items()})

    def append(self, table: str, record: dict[str, Any]) -> None:
        self._data[table].append(record)
        self._flush()

    def extend(self, table: str, records: list[dict[str, Any]]) -> None:
        self._data[table].extend(records)
        self._flush()

    def all(self, table: str) -> list[dict[str, Any]]:
        return list(self._data.get(table, []))

    def counts(self) -> dict[str, int]:
        return {table: len(rows) for table, rows in sorted(self._data.items())}

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
