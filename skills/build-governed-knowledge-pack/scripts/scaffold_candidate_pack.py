#!/usr/bin/env python3
"""Create a non-overwriting candidate knowledge-pack scaffold from an explicit plan."""

from __future__ import annotations

import argparse
import hashlib
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml


PACK_ID = re.compile(r"^[a-z0-9_]+$")
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SAFE_NAME = re.compile(r"^[a-z0-9_]+$")
LAYERS = {"insurance_core", "lob", "extension"}


class ScaffoldError(ValueError):
    pass


def load_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ScaffoldError(f"Expected a YAML mapping: {path}")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(root: Path, relative: str) -> Path:
    if Path(relative).is_absolute():
        raise ScaffoldError(f"Path must be repository-relative: {relative}")
    resolved_root = root.resolve()
    target = (resolved_root / relative).resolve()
    if target != resolved_root and resolved_root not in target.parents:
        raise ScaffoldError(f"Path escapes repository root: {relative}")
    return target


def require_text(plan: dict[str, Any], key: str) -> str:
    value = plan.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ScaffoldError(f"Plan field {key!r} must be non-empty text")
    return value.strip()


def validate_plan(plan: dict[str, Any]) -> None:
    pack_id = require_text(plan, "pack_id")
    version = require_text(plan, "pack_version")
    lob = require_text(plan, "lob")
    lob_directory = require_text(plan, "lob_directory")
    if not PACK_ID.fullmatch(pack_id):
        raise ScaffoldError("pack_id must contain lowercase letters, digits, and underscores only")
    if not SEMVER.fullmatch(version):
        raise ScaffoldError("pack_version must be semantic version X.Y.Z")
    if not SAFE_NAME.fullmatch(lob) or not SAFE_NAME.fullmatch(lob_directory):
        raise ScaffoldError("lob and lob_directory must be lowercase identifiers")
    for key in ("title", "owner", "geography"):
        require_text(plan, key)
    domains = plan.get("domains")
    if not isinstance(domains, list) or not domains or not all(isinstance(item, str) and item for item in domains):
        raise ScaffoldError("domains must be a non-empty string list")
    modules = plan.get("modules")
    if not isinstance(modules, list) or not modules:
        raise ScaffoldError("modules must be a non-empty list")
    module_ids: set[str] = set()
    module_paths: set[str] = set()
    for item in modules:
        if not isinstance(item, dict):
            raise ScaffoldError("Each module plan must be a mapping")
        module_id = require_text(item, "module_id")
        relative_path = require_text(item, "relative_path").replace("\\", "/")
        layer = require_text(item, "layer")
        if not PACK_ID.fullmatch(module_id) or module_id in module_ids:
            raise ScaffoldError(f"Invalid or duplicate module_id: {module_id}")
        if relative_path in module_paths or not relative_path.endswith("/module.yml"):
            raise ScaffoldError(f"Invalid or duplicate module path: {relative_path}")
        if layer not in LAYERS:
            raise ScaffoldError(f"Unsupported module layer: {layer}")
        if not isinstance(item.get("scope"), dict) or not item["scope"]:
            raise ScaffoldError(f"Module {module_id} requires explicit scope")
        module_ids.add(module_id)
        module_paths.add(relative_path)
    dimensions = plan.get("completeness_dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        raise ScaffoldError("completeness_dimensions must be a non-empty list")
    weights = [item.get("weight_percent") for item in dimensions if isinstance(item, dict)]
    if len(weights) != len(dimensions) or any(not isinstance(weight, (int, float)) for weight in weights):
        raise ScaffoldError("Every completeness dimension requires a numeric weight_percent")
    if abs(sum(weights) - 100) > 0.000001:
        raise ScaffoldError("Completeness dimension weights must total 100")


def build(repository_root: Path, plan_path: Path) -> Path:
    plan = load_mapping(plan_path)
    validate_plan(plan)
    root = repository_root.resolve()
    pack_id = plan["pack_id"]
    version = str(plan["pack_version"])
    lob_directory = plan["lob_directory"]
    pack_relative = f"knowledge/packs/{pack_id}/{version}"
    pack_root = inside(root, pack_relative)
    source_relative = plan.get(
        "source_registry_path",
        f"knowledge/sources/{pack_id}_v{version.replace('.', '_')}.yml",
    )
    source_path = inside(root, str(source_relative))
    if pack_root.exists():
        raise ScaffoldError(f"Refusing to overwrite existing pack version: {pack_root}")
    if source_path.exists():
        raise ScaffoldError(f"Refusing to overwrite existing source registry: {source_path}")

    for relative in (
        "glossary",
        "code_sets",
        "standards",
        "references/ontology",
        "references/target_reference_models",
        "insurance_core",
        lob_directory,
        "extensions/jurisdiction",
        "extensions/enterprise",
        "extensions/product",
        "extensions/platform",
    ):
        (pack_root / relative).mkdir(parents=True, exist_ok=True)

    created_at = str(plan.get("created_at") or date.today().isoformat())
    sources = plan.get("seed_sources", [])
    if not isinstance(sources, list):
        raise ScaffoldError("seed_sources must be a list")
    source_registry = {
        "schema_version": "1.0",
        "registry_id": f"{pack_id}_sources",
        "registry_version": version,
        "approval_state": "CANDIDATE",
        "runtime_eligible": False,
        "verified_at": created_at,
        "sources": sources,
    }
    write_yaml(source_path, source_registry)

    completeness_relative = f"{pack_relative}/completeness.yml"
    completeness_path = inside(root, completeness_relative)
    dimensions = [
        {
            "dimension": item["dimension"],
            "weight_percent": item["weight_percent"],
            "coverage_percent": 0,
            "gaps": ["not_yet_assessed"],
        }
        for item in plan["completeness_dimensions"]
    ]
    completeness = {
        "schema_version": "1.0",
        "pack_id": pack_id,
        "pack_version": version,
        "content_completeness_percent": 0,
        "trusted_runtime_readiness_percent": 0,
        "assessment_confidence": "LOW",
        "scoring_method": {
            "method": "weighted_dimension_mean_rounded_to_nearest_integer",
            "unrounded_weighted_score": 0.0,
        },
        "dimensions": dimensions,
    }
    write_yaml(completeness_path, completeness)

    module_entries: list[dict[str, str]] = []
    for item in plan["modules"]:
        module_relative = f"{pack_relative}/{item['relative_path'].replace(chr(92), '/')}"
        module_path = inside(root, module_relative)
        module = {
            "schema_version": "1.0",
            "module_id": item["module_id"],
            "module_version": version,
            "layer": item["layer"],
            "approval_state": "CANDIDATE",
            "runtime_eligible": False,
            "owner": item.get("owner", plan["owner"]),
            "scope": item["scope"],
            "non_scope": item.get("non_scope", []),
            "content": {"claims": item.get("claims", [])},
            "source_references": item.get("source_references", []),
            "dependencies": item.get("dependencies", []),
            "review_requirements": item.get("review_requirements", []),
        }
        write_yaml(module_path, module)
        module_entries.append(
            {"module_id": item["module_id"], "path": module_relative, "sha256": sha256(module_path)}
        )

    asset_paths = [completeness_relative, str(source_relative).replace("\\", "/")]
    asset_entries = [{"path": path, "sha256": sha256(inside(root, path))} for path in asset_paths]
    manifest = {
        "schema_version": "1.0",
        "pack_id": pack_id,
        "pack_version": version,
        "title": plan["title"],
        "approval_state": "CANDIDATE",
        "runtime_eligible": False,
        "immutable": True,
        "created_at": created_at,
        "owner": plan["owner"],
        "scope": {"geography": plan["geography"], "lob": plan["lob"], "domains": plan["domains"]},
        "precedence": plan.get("precedence", []),
        "source_registry": str(source_relative).replace("\\", "/"),
        "completeness": completeness_relative,
        "standards": [],
        "references": [],
        "modules": module_entries,
        "assets": asset_entries,
        "prohibitions": plan.get("prohibitions", []),
    }
    manifest_path = pack_root / "manifest.yml"
    write_yaml(manifest_path, manifest)
    print(f"created_candidate_pack={pack_relative}")
    print(f"manifest={manifest_path.relative_to(root).as_posix()}")
    print(f"source_registry={source_path.relative_to(root).as_posix()}")
    print(f"module_count={len(module_entries)}")
    print("approval_state=CANDIDATE runtime_eligible=false")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    args = parser.parse_args()
    try:
        build(args.repository_root, args.plan)
    except (OSError, ScaffoldError, yaml.YAMLError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
