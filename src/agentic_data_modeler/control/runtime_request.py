"""Fail-closed parsing for one bounded source-discovery execution request."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Mapping

from .source_scope import SourceScopeMode, validate_patterns


# The machine-readable Increment-1 inventory is the approved contract-set
# identity. It pins all 31 record versions and common_ref 0.3.0.
APPROVED_CONTRACT_SET_VERSION = "0.2.0"

_IDENTIFIER = re.compile(r"^[A-Za-z0-9_]+$")
_SEMANTIC_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_PLACEHOLDER_PREFIXES = ("REQUIRED_", "TODO", "TBD")
_MAX_TEXT_LENGTH = 256


class RuntimeRequestError(ValueError):
    """Raised before source access when runtime scope is unsafe or incomplete."""


class ProfilingMode(StrEnum):
    """Profiling modes currently authorized by profile_snapshot contract 0.1.0."""

    FULL = "FULL"
    METADATA_ONLY = "METADATA_ONLY"
    RESTRICTED = "RESTRICTED"


def _required_text(parameters: Mapping[str, Any], name: str) -> str:
    raw = parameters.get(name)
    if not isinstance(raw, str):
        raise RuntimeRequestError(f"{name} must be a string")
    value = raw.strip()
    if not value:
        raise RuntimeRequestError(f"{name} is required")
    if value.upper().startswith(_PLACEHOLDER_PREFIXES):
        raise RuntimeRequestError(f"{name} contains an unresolved placeholder")
    if len(value) > _MAX_TEXT_LENGTH:
        raise RuntimeRequestError(f"{name} exceeds {_MAX_TEXT_LENGTH} characters")
    if any(character in value for character in ("\x00", "\r", "\n")):
        raise RuntimeRequestError(f"{name} contains a prohibited control character")
    return value


def _optional_text(parameters: Mapping[str, Any], name: str) -> str | None:
    raw = parameters.get(name)
    if raw is None or raw == "":
        return None
    return _required_text(parameters, name)


def _identifier(parameters: Mapping[str, Any], name: str) -> str:
    value = _required_text(parameters, name)
    if not _IDENTIFIER.fullmatch(value):
        raise RuntimeRequestError(f"{name} is not a safe unqualified identifier")
    return value


def _parse_json_string_array(
    raw: Any,
    *,
    name: str,
    allow_empty: bool,
) -> tuple[str, ...]:
    if not isinstance(raw, str):
        raise RuntimeRequestError(f"{name} must be a JSON array string")
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeRequestError(f"{name} must be valid JSON") from exc
    if not isinstance(decoded, list) or (not allow_empty and not decoded):
        qualifier = "" if allow_empty else "non-empty "
        raise RuntimeRequestError(f"{name} must be a {qualifier}JSON array")
    if not all(isinstance(item, str) for item in decoded):
        raise RuntimeRequestError(f"{name} entries must be strings")

    values = tuple(item.strip() for item in decoded)
    if any(not value for value in values):
        raise RuntimeRequestError(f"{name} entries must not be empty")
    if len(values) != len(set(values)):
        raise RuntimeRequestError(f"{name} contains duplicates")
    return values


def _parse_source_tables(raw: Any, *, allow_empty: bool) -> tuple[str, ...]:
    tables = _parse_json_string_array(raw, name="source_tables", allow_empty=allow_empty)
    unsafe = [table for table in tables if not _IDENTIFIER.fullmatch(table)]
    if unsafe:
        raise RuntimeRequestError(f"source_tables contains unsafe identifiers: {unsafe}")
    return tables


@dataclass(frozen=True, slots=True)
class RuntimeRequest:
    """Validated runtime boundary for exactly one source-discovery work package."""

    run_id: str
    engagement_id: str
    work_package_id: str
    lob: str
    domain: str
    source_catalog: str
    source_schema: str
    source_scope_mode: SourceScopeMode
    source_table_include_patterns: tuple[str, ...]
    source_table_exclude_patterns: tuple[str, ...]
    source_object_types: tuple[str, ...]
    source_tables: tuple[str, ...]
    source_system_id: str
    source_product: str | None
    source_module: str | None
    source_version: str | None
    profiling_mode: ProfilingMode
    profiling_policy_id: str
    profiling_policy_version: str
    document_set_id: str | None
    requirement_set_id: str | None
    output_catalog: str
    output_schema: str
    contract_set_version: str

    @classmethod
    def from_parameters(cls, parameters: Mapping[str, Any]) -> "RuntimeRequest":
        """Parse job parameters and reject unsafe scope before any source read."""

        source_catalog = _identifier(parameters, "source_catalog")
        source_schema = _identifier(parameters, "source_schema")
        output_catalog = _identifier(parameters, "output_catalog")
        output_schema = _identifier(parameters, "output_schema")
        if (source_catalog.casefold(), source_schema.casefold()) == (
            output_catalog.casefold(),
            output_schema.casefold(),
        ):
            raise RuntimeRequestError("source and output schema boundaries must be distinct")

        scope_mode_value = _required_text(parameters, "source_scope_mode")
        try:
            source_scope_mode = SourceScopeMode(scope_mode_value)
        except ValueError as exc:
            allowed = ", ".join(mode.value for mode in SourceScopeMode)
            raise RuntimeRequestError(f"source_scope_mode must be one of: {allowed}") from exc

        try:
            include_patterns = validate_patterns(
                _parse_json_string_array(
                    parameters.get("source_table_include_patterns"),
                    name="source_table_include_patterns",
                    allow_empty=True,
                ),
                field_name="source_table_include_patterns",
            )
            exclude_patterns = validate_patterns(
                _parse_json_string_array(
                    parameters.get("source_table_exclude_patterns"),
                    name="source_table_exclude_patterns",
                    allow_empty=True,
                ),
                field_name="source_table_exclude_patterns",
            )
        except ValueError as exc:
            raise RuntimeRequestError(str(exc)) from exc
        object_types = _parse_json_string_array(
            parameters.get("source_object_types"),
            name="source_object_types",
            allow_empty=False,
        )
        allowed_object_types = {"TABLE", "VIEW", "MATERIALIZED_VIEW"}
        if not set(object_types).issubset(allowed_object_types):
            raise RuntimeRequestError(
                f"source_object_types must be a subset of: {sorted(allowed_object_types)}"
            )
        source_tables = _parse_source_tables(
            parameters.get("source_tables"),
            allow_empty=source_scope_mode is not SourceScopeMode.EXPLICIT_TABLES,
        )
        if source_scope_mode is SourceScopeMode.EXPLICIT_TABLES and (
            include_patterns or exclude_patterns
        ):
            raise RuntimeRequestError(
                "EXPLICIT_TABLES does not accept include or exclude patterns"
            )

        mode_value = _required_text(parameters, "run_mode")
        try:
            profiling_mode = ProfilingMode(mode_value)
        except ValueError as exc:
            allowed = ", ".join(mode.value for mode in ProfilingMode)
            raise RuntimeRequestError(f"run_mode must be one of: {allowed}") from exc

        policy_version = _required_text(parameters, "profiling_policy_version")
        if not _SEMANTIC_VERSION.fullmatch(policy_version):
            raise RuntimeRequestError("profiling_policy_version must be semantic version X.Y.Z")

        contract_set_version = _required_text(parameters, "contract_set_version")
        if contract_set_version != APPROVED_CONTRACT_SET_VERSION:
            raise RuntimeRequestError(
                "contract_set_version must exactly match the approved Increment-1 contract set"
            )

        return cls(
            run_id=_required_text(parameters, "run_id"),
            engagement_id=_required_text(parameters, "engagement_id"),
            work_package_id=_required_text(parameters, "work_package_id"),
            lob=_required_text(parameters, "lob"),
            domain=_required_text(parameters, "domain"),
            source_catalog=source_catalog,
            source_schema=source_schema,
            source_scope_mode=source_scope_mode,
            source_table_include_patterns=include_patterns,
            source_table_exclude_patterns=exclude_patterns,
            source_object_types=object_types,
            source_tables=source_tables,
            source_system_id=_required_text(parameters, "source_system_id"),
            source_product=_optional_text(parameters, "source_product"),
            source_module=_optional_text(parameters, "source_module"),
            source_version=_optional_text(parameters, "source_version"),
            profiling_mode=profiling_mode,
            profiling_policy_id=_required_text(parameters, "profiling_policy_id"),
            profiling_policy_version=policy_version,
            document_set_id=_optional_text(parameters, "document_set_id"),
            requirement_set_id=_optional_text(parameters, "requirement_set_id"),
            output_catalog=output_catalog,
            output_schema=output_schema,
            contract_set_version=contract_set_version,
        )

    def canonical_payload(self) -> str:
        """Return stable JSON for the logical request, independent of execution."""

        payload = asdict(self)
        payload.pop("run_id")
        payload["profiling_mode"] = self.profiling_mode.value
        payload["source_scope_mode"] = self.source_scope_mode.value
        payload["source_table_include_patterns"] = sorted(self.source_table_include_patterns)
        payload["source_table_exclude_patterns"] = sorted(self.source_table_exclude_patterns)
        payload["source_object_types"] = sorted(self.source_object_types)
        payload["source_tables"] = sorted(self.source_tables)
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def fingerprint(self) -> str:
        """Return a deterministic SHA-256 fingerprint of the logical request."""

        return hashlib.sha256(self.canonical_payload().encode("utf-8")).hexdigest()
