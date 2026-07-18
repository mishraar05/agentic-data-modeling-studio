"""Deterministic resolution of an authorized source scope into a frozen manifest."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_]+$")
_SAFE_PATTERN = re.compile(r"^[A-Za-z0-9_*?]+$")


class SourceScopeError(ValueError):
    """Raised before row access when a source scope cannot be resolved safely."""


class SourceScopeMode(StrEnum):
    """Supported ways to select source objects within an authorized schema."""

    EXPLICIT_TABLES = "EXPLICIT_TABLES"
    SCHEMA_ALL_TABLES = "SCHEMA_ALL_TABLES"
    PATTERN_BASED = "PATTERN_BASED"


@dataclass(frozen=True, slots=True)
class SourceObjectCandidate:
    """One metadata-visible source object eligible for deterministic selection."""

    name: str
    object_type: str


@dataclass(frozen=True, slots=True)
class ResolvedSourceManifest:
    """Immutable result of applying a source-scope policy to visible metadata."""

    catalog: str
    schema: str
    scope_mode: SourceScopeMode
    include_patterns: tuple[str, ...]
    exclude_patterns: tuple[str, ...]
    object_types: tuple[str, ...]
    tables: tuple[str, ...]
    resolver_version: str = "uc-schema-scope/0.1.0"

    def canonical_payload(self) -> str:
        return json.dumps(
            {
                "catalog": self.catalog,
                "schema": self.schema,
                "scope_mode": self.scope_mode.value,
                "include_patterns": sorted(self.include_patterns),
                "exclude_patterns": sorted(self.exclude_patterns),
                "object_types": sorted(self.object_types),
                "tables": list(self.tables),
                "resolver_version": self.resolver_version,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_payload().encode("utf-8")).hexdigest()


def validate_patterns(patterns: Iterable[str], *, field_name: str) -> tuple[str, ...]:
    """Validate simple case-sensitive glob patterns without SQL fragments."""

    values = tuple(pattern.strip() for pattern in patterns)
    if any(not value for value in values):
        raise SourceScopeError(f"{field_name} contains an empty pattern")
    if len(values) != len(set(values)):
        raise SourceScopeError(f"{field_name} contains duplicate patterns")
    unsafe = [value for value in values if not _SAFE_PATTERN.fullmatch(value)]
    if unsafe:
        raise SourceScopeError(f"{field_name} contains unsafe patterns: {unsafe}")
    return values


def resolve_source_manifest(
    *,
    catalog: str,
    schema: str,
    scope_mode: SourceScopeMode,
    visible_objects: Iterable[SourceObjectCandidate],
    explicit_tables: Iterable[str],
    include_patterns: Iterable[str],
    exclude_patterns: Iterable[str],
    object_types: Iterable[str],
) -> ResolvedSourceManifest:
    """Resolve visible metadata to the exact source manifest for one execution."""

    explicit = tuple(explicit_tables)
    includes = validate_patterns(include_patterns, field_name="source_table_include_patterns")
    excludes = validate_patterns(exclude_patterns, field_name="source_table_exclude_patterns")
    allowed_types = tuple(sorted(set(object_types)))
    if not allowed_types:
        raise SourceScopeError("source_object_types must not be empty")

    candidates = tuple(visible_objects)
    names = [candidate.name for candidate in candidates]
    if len(names) != len(set(names)):
        raise SourceScopeError("source metadata contains duplicate object names")
    unsafe_names = sorted(name for name in names if not _SAFE_IDENTIFIER.fullmatch(name))
    if unsafe_names:
        raise SourceScopeError(
            "eligible source objects contain identifiers unsupported by the current contract: "
            f"{unsafe_names}"
        )

    eligible = {
        candidate.name
        for candidate in candidates
        if candidate.object_type in allowed_types
    }
    if scope_mode is SourceScopeMode.EXPLICIT_TABLES:
        if not explicit:
            raise SourceScopeError("EXPLICIT_TABLES requires at least one source table")
        missing = sorted(set(explicit) - eligible)
        if missing:
            raise SourceScopeError(f"explicit source tables are not visible or eligible: {missing}")
        selected = set(explicit)
    else:
        if explicit:
            raise SourceScopeError(
                f"{scope_mode.value} resolves tables from metadata; source_tables must be empty"
            )
        effective_includes = includes or ("*",)
        selected = {
            name
            for name in eligible
            if any(fnmatch.fnmatchcase(name, pattern) for pattern in effective_includes)
            and not any(fnmatch.fnmatchcase(name, pattern) for pattern in excludes)
        }
        if scope_mode is SourceScopeMode.SCHEMA_ALL_TABLES and includes not in {(), ("*",)}:
            raise SourceScopeError(
                "SCHEMA_ALL_TABLES permits only the implicit or explicit '*' include pattern"
            )

    if not selected:
        raise SourceScopeError("source-scope policy resolved to zero eligible tables")

    return ResolvedSourceManifest(
        catalog=catalog,
        schema=schema,
        scope_mode=scope_mode,
        include_patterns=includes or ("*",),
        exclude_patterns=excludes,
        object_types=allowed_types,
        tables=tuple(sorted(selected)),
    )
