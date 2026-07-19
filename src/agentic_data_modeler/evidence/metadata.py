"""Exact validation and fingerprinting for a Unity Catalog metadata inventory."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Iterable


class MetadataInventoryError(ValueError):
    """Raised when observed metadata does not reconcile to the frozen manifest."""


def stable_record_id(prefix: str, *parts: str) -> str:
    """Build a stable identifier without embedding physical names in the ID."""

    content = json.dumps(parts, ensure_ascii=True, separators=(",", ":"))
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:32]}"


def one_based_ordinal_offset(positions: Iterable[int]) -> int:
    """Return the deterministic offset needed to express ordinals as 1-based."""

    values = tuple(int(position) for position in positions)
    if not values:
        raise MetadataInventoryError("Cannot normalize an empty ordinal sequence")
    if len(values) != len(set(values)) or min(values) < 0:
        raise MetadataInventoryError("Source metadata contains invalid ordinal positions")
    return 1 if min(values) == 0 else 0


@dataclass(frozen=True, slots=True)
class ConstraintMetadata:
    name: str
    constraint_type: str
    columns: tuple[str, ...] = ()

    def canonical(self) -> dict:
        return {
            "name": self.name,
            "constraint_type": self.constraint_type,
            "columns": sorted(self.columns),
        }


@dataclass(frozen=True, slots=True)
class ColumnMetadata:
    name: str
    ordinal_position: int
    data_type: str
    nullable: bool
    default_value: str | None = None
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    constraint_types: tuple[str, ...] = ()

    def constraint_role(self) -> str:
        normalized = {value.upper().replace(" ", "_") for value in self.constraint_types}
        for role in ("PRIMARY_KEY", "FOREIGN_KEY", "UNIQUE", "CHECK"):
            if role in normalized:
                return role
        return "NONE"

    def canonical(self) -> dict:
        payload = asdict(self)
        payload["constraint_types"] = sorted(self.constraint_types)
        return payload


@dataclass(frozen=True, slots=True)
class ObjectMetadata:
    name: str
    object_type: str
    columns: tuple[ColumnMetadata, ...]
    constraints: tuple[ConstraintMetadata, ...] = ()

    def canonical(self) -> dict:
        return {
            "name": self.name,
            "object_type": self.object_type,
            "columns": [column.canonical() for column in sorted(self.columns, key=lambda item: item.ordinal_position)],
            "constraints": [
                constraint.canonical()
                for constraint in sorted(self.constraints, key=lambda item: (item.constraint_type, item.name))
            ],
        }


@dataclass(frozen=True, slots=True)
class MetadataInventory:
    catalog: str
    schema: str
    expected_tables: tuple[str, ...]
    objects: tuple[ObjectMetadata, ...]
    query_template_version: str = "uc-information-schema-inventory/0.1.0"

    def validate(self) -> None:
        expected = set(self.expected_tables)
        if not expected or len(expected) != len(self.expected_tables):
            raise MetadataInventoryError("Expected frozen table manifest must be non-empty and unique")

        observed_names = [item.name for item in self.objects]
        if len(observed_names) != len(set(observed_names)):
            raise MetadataInventoryError("Observed metadata contains duplicate objects")
        observed = set(observed_names)
        if observed != expected:
            missing = sorted(expected - observed)
            unexpected = sorted(observed - expected)
            raise MetadataInventoryError(
                f"Metadata coverage mismatch; missing={missing}, unexpected={unexpected}"
            )

        for item in self.objects:
            if item.object_type not in {"TABLE", "VIEW", "MATERIALIZED_VIEW"}:
                raise MetadataInventoryError(f"Unsupported object type for {item.name}: {item.object_type}")
            if not item.columns:
                raise MetadataInventoryError(f"Object {item.name} has no visible columns")
            column_names = [column.name for column in item.columns]
            ordinals = [column.ordinal_position for column in item.columns]
            if len(column_names) != len(set(column_names)):
                raise MetadataInventoryError(f"Object {item.name} has duplicate columns")
            if len(ordinals) != len(set(ordinals)) or min(ordinals) < 1:
                raise MetadataInventoryError(f"Object {item.name} has invalid ordinal positions")
            known_columns = set(column_names)
            for constraint in item.constraints:
                unknown = set(constraint.columns) - known_columns
                if unknown:
                    raise MetadataInventoryError(
                        f"Constraint {constraint.name} on {item.name} references unknown columns: {sorted(unknown)}"
                    )

    @property
    def table_count(self) -> int:
        return len(self.objects)

    @property
    def column_count(self) -> int:
        return sum(len(item.columns) for item in self.objects)

    def canonical_payload(self) -> str:
        self.validate()
        payload = {
            "catalog": self.catalog,
            "schema": self.schema,
            "expected_tables": sorted(self.expected_tables),
            "objects": [item.canonical() for item in sorted(self.objects, key=lambda value: value.name)],
            "query_template_version": self.query_template_version,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_payload().encode("utf-8")).hexdigest()

    def snapshot_id(self, run_id: str) -> str:
        return stable_record_id("source_snapshot", run_id, self.fingerprint())

    def object_evidence_content(self, object_name: str) -> str:
        item = self.object_named(object_name)
        payload = {
            "catalog": self.catalog,
            "schema": self.schema,
            "object": item.canonical(),
            "query_template_version": self.query_template_version,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def object_named(self, object_name: str) -> ObjectMetadata:
        matches = [item for item in self.objects if item.name == object_name]
        if len(matches) != 1:
            raise MetadataInventoryError(f"Expected exactly one object named {object_name}")
        return matches[0]

    @classmethod
    def from_iterables(
        cls,
        *,
        catalog: str,
        schema: str,
        expected_tables: Iterable[str],
        objects: Iterable[ObjectMetadata],
    ) -> "MetadataInventory":
        return cls(
            catalog=catalog,
            schema=schema,
            expected_tables=tuple(expected_tables),
            objects=tuple(objects),
        )
