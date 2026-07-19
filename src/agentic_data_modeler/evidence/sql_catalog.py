"""Read real source metadata from a live catalog's information_schema (Phase 1 tool).

No invented schemas: this queries an actual database catalog and returns a
``MetadataInventory``. ``DuckDBCatalogReader`` is the adapter used in dev; a
``UnityCatalogReader`` implementing the same ``read_inventory`` slots in for
production against Databricks. The source location and allow-listed tables come
from configuration (the D23-01 decision), never from code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .metadata import ColumnMetadata, ConstraintMetadata, MetadataInventory, ObjectMetadata

_CONSTRAINT_MAP = {
    "PRIMARY KEY": "PRIMARY_KEY", "FOREIGN KEY": "FOREIGN_KEY",
    "UNIQUE": "UNIQUE", "CHECK": "CHECK",
}
_OBJECT_TYPE_MAP = {"BASE TABLE": "TABLE", "TABLE": "TABLE", "VIEW": "VIEW",
                    "MATERIALIZED VIEW": "MATERIALIZED_VIEW"}


class CatalogReader(Protocol):
    def read_inventory(self, *, catalog: str, schema: str,
                       tables: list[str]) -> MetadataInventory: ...


class DuckDBCatalogReader:
    """information_schema reader for a DuckDB database (real catalog, read-only)."""

    def __init__(self, database: str | Path):
        self.database = str(database)

    def read_inventory(self, *, catalog: str, schema: str, tables: list[str]) -> MetadataInventory:
        import duckdb

        allow = set(tables)
        con = duckdb.connect(self.database, read_only=True)
        try:
            table_types = {
                name: _OBJECT_TYPE_MAP.get(str(ttype).upper(), "TABLE")
                for name, ttype in con.execute(
                    "SELECT table_name, table_type FROM information_schema.tables "
                    "WHERE table_schema = ?", [schema]).fetchall()
                if name in allow
            }
            col_rows = con.execute(
                "SELECT table_name, column_name, ordinal_position, data_type, is_nullable, "
                "column_default, character_maximum_length, numeric_precision, numeric_scale "
                "FROM information_schema.columns WHERE table_schema = ? "
                "ORDER BY table_name, ordinal_position", [schema]).fetchall()
            constraint_rows = con.execute(
                "SELECT table_name, constraint_type, constraint_column_names "
                "FROM duckdb_constraints() WHERE schema_name = ?", [schema]).fetchall()
        finally:
            con.close()

        # column constraint roles + object-level constraints
        col_roles: dict[tuple[str, str], set[str]] = {}
        obj_constraints: dict[str, list[ConstraintMetadata]] = {}
        for table_name, ctype, columns in constraint_rows:
            if table_name not in allow:
                continue
            mapped = _CONSTRAINT_MAP.get(str(ctype).upper())
            if not mapped:
                continue
            cols = tuple(columns or ())
            obj_constraints.setdefault(table_name, []).append(
                ConstraintMetadata(name=f"{table_name}_{mapped.lower()}", constraint_type=mapped, columns=cols))
            for col in cols:
                col_roles.setdefault((table_name, col), set()).add(mapped)

        columns_by_table: dict[str, list[ColumnMetadata]] = {}
        for (tname, cname, ordinal, dtype, is_nullable, default, length, precision, scale) in col_rows:
            if tname not in allow:
                continue
            columns_by_table.setdefault(tname, []).append(ColumnMetadata(
                name=cname, ordinal_position=int(ordinal), data_type=str(dtype),
                nullable=str(is_nullable).upper() == "YES",
                default_value=None if default is None else str(default),
                length=None if length is None else int(length),
                precision=None if precision is None else int(precision),
                scale=None if scale is None else int(scale),
                constraint_types=tuple(sorted(col_roles.get((tname, cname), set()))),
            ))

        missing = allow - set(columns_by_table)
        if missing:
            raise LookupError(f"Allow-listed tables not found in {schema}: {sorted(missing)}")

        objects = tuple(
            ObjectMetadata(
                name=tname, object_type=table_types.get(tname, "TABLE"),
                columns=tuple(columns_by_table[tname]),
                constraints=tuple(obj_constraints.get(tname, [])),
            )
            for tname in sorted(allow)
        )
        return MetadataInventory.from_iterables(
            catalog=catalog, schema=schema, expected_tables=tuple(sorted(allow)), objects=objects)
