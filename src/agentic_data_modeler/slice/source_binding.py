"""Load the proof-slice source binding from config (D23-01 / D23-02).

Turns config/proof_slice.yaml into a live catalog reader + run scope, so the
source and identities live in configuration, never hardcoded in the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..evidence.sql_catalog import CatalogReader, DuckDBCatalogReader
from .records import Scope


@dataclass(slots=True)
class ProofSliceBinding:
    reader: CatalogReader
    catalog: str
    schema: str
    tables: list[str]
    lob: str
    domain: str
    pack_id: str
    pack_version: str
    geography: str
    pack_domains: set[str]

    def read_inventory(self):
        return self.reader.read_inventory(catalog=self.catalog, schema=self.schema, tables=self.tables)

    def scope(self, *, run_id: str) -> Scope:
        return Scope(lob=self.lob, domain=self.domain, run_id=run_id,
                     memory_partition=f"{self.catalog}.{self.schema}")


def _make_reader(root: Path, source: dict[str, Any]) -> CatalogReader:
    engine = source.get("engine", "duckdb")
    if engine == "duckdb":
        return DuckDBCatalogReader(root / source["database"])
    raise ValueError(f"Unsupported source engine '{engine}'. Add a CatalogReader adapter.")


def load_binding(root: Path, config_path: str = "config/proof_slice.yaml") -> ProofSliceBinding:
    root = Path(root)
    cfg = yaml.safe_load((root / config_path).read_text(encoding="utf-8"))
    source, scope, pack = cfg["source"], cfg["scope"], cfg["knowledge_pack"]
    return ProofSliceBinding(
        reader=_make_reader(root, source),
        catalog=source["catalog"], schema=source["schema"],
        tables=list(source["allow_listed_tables"]),
        lob=scope["lob"], domain=scope["domain"],
        pack_id=pack["pack_id"], pack_version=str(pack["pack_version"]),
        geography=pack["geography"], pack_domains=set(pack["pack_domains"]),
    )
