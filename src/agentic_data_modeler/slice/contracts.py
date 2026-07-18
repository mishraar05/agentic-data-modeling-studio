"""Validate records against the real contracts/*.schema.json (cross-$ref aware)."""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


class ContractViolation(ValueError):
    """Raised when a record fails its contract."""


@functools.lru_cache(maxsize=8)
def _load(root_str: str) -> tuple[dict[str, dict], Registry]:
    root = Path(root_str)
    schemas: dict[str, dict] = {}
    for path in sorted((root / "contracts").glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        schemas[schema["$id"]] = schema
    registry = Registry().with_resources(
        [(sid, Resource.from_contents(schema)) for sid, schema in schemas.items()]
    )
    return schemas, registry


def validation_errors(repo_root: Path, contract_id: str, record: dict[str, Any]) -> list[str]:
    """Return a list of human-readable contract violations ([] means valid)."""
    schemas, registry = _load(str(Path(repo_root).resolve()))
    if contract_id not in schemas:
        raise KeyError(f"Unknown contract id: {contract_id}")
    validator = Draft202012Validator(
        schemas[contract_id], registry=registry, format_checker=FormatChecker()
    )
    return [
        f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
        for err in sorted(validator.iter_errors(record), key=lambda e: list(e.path))
    ]


def require_valid(repo_root: Path, contract_id: str, record: dict[str, Any]) -> dict[str, Any]:
    """Validate and return the record, or raise ContractViolation. Fail-closed."""
    errors = validation_errors(repo_root, contract_id, record)
    if errors:
        raise ContractViolation(
            f"{contract_id} invalid:\n  - " + "\n  - ".join(errors)
        )
    return record
