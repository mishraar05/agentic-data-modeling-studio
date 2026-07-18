"""Fail-closed parsing for one bounded source-discovery execution request."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Mapping


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


def _parse_source_tables(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, str):
        raise RuntimeRequestError("source_tables must be a JSON array string")
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeRequestError("source_tables must be valid JSON") from exc
    if not isinstance(decoded, list) or not decoded:
        raise RuntimeRequestError("source_tables must be a non-empty JSON array")
    if not all(isinstance(item, str) for item in decoded):
        raise RuntimeRequestError("source_tables entries must be strings")

    tables = tuple(item.strip() for item in decoded)
    if any(not table for table in tables):
        raise RuntimeRequestError("source_tables entries must not be empty")
    if len(tables) != len(set(tables)):
        raise RuntimeRequestError("source_tables contains duplicates")
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
            source_tables=_parse_source_tables(parameters.get("source_tables")),
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
        payload["source_tables"] = sorted(self.source_tables)
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def fingerprint(self) -> str:
        """Return a deterministic SHA-256 fingerprint of the logical request."""

        return hashlib.sha256(self.canonical_payload().encode("utf-8")).hexdigest()
