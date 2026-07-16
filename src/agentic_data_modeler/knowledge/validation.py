"""Deterministic validation for versioned knowledge packs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


class KnowledgeValidationError(ValueError):
    """Raised when governed knowledge fails a structural or integrity check."""


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise KnowledgeValidationError(f"Expected a mapping in {path}")
    return data


def resolve_inside(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    candidate = (root / relative_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise KnowledgeValidationError(f"Path escapes repository root: {relative_path}")
    return candidate


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_schema(instance: dict[str, Any], schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.path))
    if errors:
        detail = "; ".join(error.message for error in errors)
        raise KnowledgeValidationError(f"Schema validation failed for {schema_path.name}: {detail}")


def validate_repository_pack(repository_root: Path, manifest_relative_path: str) -> dict[str, Any]:
    """Validate a pack without granting runtime eligibility."""

    root = repository_root.resolve()
    manifest_path = resolve_inside(root, manifest_relative_path)
    manifest = load_yaml(manifest_path)
    validate_schema(manifest, root / "knowledge/schemas/pack_manifest.schema.json")

    known_sources: set[str] | None = None
    source_registry_path_value = manifest.get("source_registry")
    if source_registry_path_value:
        source_registry_path = resolve_inside(root, source_registry_path_value)
        source_registry = load_yaml(source_registry_path)
        validate_schema(source_registry, root / "knowledge/schemas/source_registry.schema.json")
        if source_registry["registry_version"] != manifest["pack_version"]:
            raise KnowledgeValidationError("Source registry version differs from pack version")
        if source_registry["approval_state"] != manifest["approval_state"]:
            raise KnowledgeValidationError("Source registry approval state differs from pack")
        if source_registry["runtime_eligible"] != manifest["runtime_eligible"]:
            raise KnowledgeValidationError("Source registry runtime eligibility differs from pack")
        source_ids = [item["source_id"] for item in source_registry["sources"]]
        if len(source_ids) != len(set(source_ids)):
            raise KnowledgeValidationError("Source registry contains duplicate source IDs")
        known_sources = set(source_ids)

    seen_modules: set[str] = set()
    for entry in manifest["modules"]:
        module_path = resolve_inside(root, entry["path"])
        if not module_path.is_file():
            raise KnowledgeValidationError(f"Missing module: {entry['path']}")
        if sha256(module_path) != entry["sha256"]:
            raise KnowledgeValidationError(f"Module fingerprint mismatch: {entry['path']}")
        module = load_yaml(module_path)
        validate_schema(module, root / "knowledge/schemas/module.schema.json")
        if module["module_id"] != entry["module_id"]:
            raise KnowledgeValidationError(f"Module identity mismatch: {entry['path']}")
        if module["module_id"] in seen_modules:
            raise KnowledgeValidationError(f"Duplicate module identity: {module['module_id']}")
        if known_sources is not None:
            unknown_sources = set(module["source_references"]) - known_sources
            if unknown_sources:
                raise KnowledgeValidationError(
                    f"Module {module['module_id']} references unknown sources: {sorted(unknown_sources)}"
                )
        seen_modules.add(module["module_id"])

    asset_paths = {entry["path"] for entry in manifest["assets"]}
    if source_registry_path_value and source_registry_path_value not in asset_paths:
        raise KnowledgeValidationError("Source registry must be a fingerprinted manifest asset")
    if manifest.get("completeness") not in asset_paths:
        raise KnowledgeValidationError("Completeness assessment must be a fingerprinted manifest asset")

    for entry in manifest["assets"]:
        asset_path = resolve_inside(root, entry["path"])
        if not asset_path.is_file():
            raise KnowledgeValidationError(f"Missing asset: {entry['path']}")
        if sha256(asset_path) != entry["sha256"]:
            raise KnowledgeValidationError(f"Asset fingerprint mismatch: {entry['path']}")

    completeness_path = resolve_inside(root, manifest["completeness"])
    completeness = load_yaml(completeness_path)
    validate_schema(completeness, root / "knowledge/schemas/completeness.schema.json")
    if completeness["pack_id"] != manifest["pack_id"] or completeness["pack_version"] != manifest["pack_version"]:
        raise KnowledgeValidationError("Completeness assessment targets a different pack")
    if sum(item["weight_percent"] for item in completeness["dimensions"]) != 100:
        raise KnowledgeValidationError("Completeness dimension weights must total 100")

    return manifest
