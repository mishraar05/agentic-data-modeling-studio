"""Build the proof-slice DuckDB source from the SQL fixture (test data helper).

Idempotent: rebuilds the DuckDB file from proof_slice_source.sql so tests read a
real catalog via information_schema instead of any hardcoded schema.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).resolve().parent
SQL_FILE = FIXTURES / "proof_slice_source.sql"


def build(database_path: str | Path) -> Path:
    import duckdb

    db = Path(database_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    try:
        con.execute("DROP SCHEMA IF EXISTS gw_pc_bronze CASCADE;")  # idempotent, no unlink
        con.execute(SQL_FILE.read_text(encoding="utf-8"))
    finally:
        con.close()
    return db


if __name__ == "__main__":
    print("built:", build(FIXTURES / "proof_slice_source.duckdb"))
