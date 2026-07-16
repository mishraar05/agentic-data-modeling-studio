#!/usr/bin/env python3
"""Finalize fingerprints and strictly validate a governed candidate knowledge pack."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml


DERIVATION_TYPES = {
    "exact_structured_fact",
    "independent_paraphrase",
    "modeling_inference",
    "sme_decision",
}
EFFECTIVE_DATE_STATES = {"KNOWN", "NOT_APPLICABLE", "UNRESOLVED"}


class CandidateValidationError(ValueError):
    pass


def load_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CandidateValidationError(f"Expected a YAML mapping: {path}")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_inside(root: Path, relative: str) -> Path:
    root = root.resolve()
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise CandidateValidationError(f"Path escapes repository root: {relative}")
    return candidate


def strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise CandidateValidationError(f"{field} must be a list of non-empty strings")
    return value


def collect_source_ids(node: Any) -> Iterable[str]:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"source_ids", "source_references"}:
                yield from strings(value, key)
            elif key == "source_reference":
                if not isinstance(value, str) or not value:
                    raise CandidateValidationError("source_reference must be non-empty text")
                yield value
            else:
                yield from collect_source_ids(value)
    elif isinstance(node, list):
        for value in node:
            yield from collect_source_ids(value)


def validate_claims(module: dict[str, Any], known_sources: set[str]) -> int:
    content = module.get("content")
    claims = content.get("claims") if isinstance(content, dict) else None
    if not isinstance(claims, list) or not claims:
        raise CandidateValidationError(
            f"Module {module.get('module_id')} requires non-empty content.claims for strict provenance"
        )
    seen: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict):
            raise CandidateValidationError("Every claim must be a mapping")
        claim_id = claim.get("claim_id")
        statement = claim.get("statement")
        derivation = claim.get("derivation_type")
        applicability = claim.get("applicability")
        if not isinstance(claim_id, str) or not claim_id or claim_id in seen:
            raise CandidateValidationError(f"Invalid or duplicate claim_id: {claim_id!r}")
        if not isinstance(statement, str) or not statement.strip():
            raise CandidateValidationError(f"Claim {claim_id} requires a statement")
        if derivation not in DERIVATION_TYPES:
            raise CandidateValidationError(f"Claim {claim_id} has invalid derivation_type")
        if not isinstance(applicability, str) or not applicability.strip():
            raise CandidateValidationError(f"Claim {claim_id} requires applicability")
        source_ids = claim.get("source_ids", [])
        decisions = claim.get("decision_references", [])
        if derivation == "sme_decision":
            if not strings(decisions, f"{claim_id}.decision_references"):
                raise CandidateValidationError(f"SME decision claim {claim_id} requires decision references")
        else:
            resolved = strings(source_ids, f"{claim_id}.source_ids")
            unknown = set(resolved) - known_sources
            if unknown:
                raise CandidateValidationError(f"Claim {claim_id} references unknown sources: {sorted(unknown)}")
        if derivation == "exact_structured_fact" and not claim.get("source_locator"):
            raise CandidateValidationError(f"Exact fact {claim_id} requires source_locator")
        if claim.get("jurisdiction"):
            state = claim.get("effective_date_status")
            if state not in EFFECTIVE_DATE_STATES:
                raise CandidateValidationError(f"Jurisdiction claim {claim_id} requires effective_date_status")
            if state == "KNOWN" and not claim.get("effective_from"):
                raise CandidateValidationError(f"Jurisdiction claim {claim_id} requires effective_from")
        seen.add(claim_id)
    return len(claims)


def validate_and_finalize(root: Path, manifest_relative: str) -> None:
    root = root.resolve()
    manifest_path = resolve_inside(root, manifest_relative)
    manifest = load_mapping(manifest_path)
    if manifest.get("approval_state") != "CANDIDATE" or manifest.get("runtime_eligible") is not False:
        raise CandidateValidationError("Finalizer accepts only CANDIDATE, non-runtime packs")
    if manifest.get("immutable") is not True:
        raise CandidateValidationError("Candidate manifest must declare immutable: true")

    source_relative = manifest.get("source_registry")
    if not isinstance(source_relative, str) or not source_relative:
        raise CandidateValidationError("Manifest requires source_registry")
    source_registry = load_mapping(resolve_inside(root, source_relative))
    if source_registry.get("approval_state") != "CANDIDATE" or source_registry.get("runtime_eligible") is not False:
        raise CandidateValidationError("Source registry must remain CANDIDATE and non-runtime")
    sources = source_registry.get("sources")
    if not isinstance(sources, list):
        raise CandidateValidationError("Source registry sources must be a list")
    known_sources: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise CandidateValidationError("Every source must be a mapping")
        required = ("source_id", "publisher", "url", "source_class", "usage_basis")
        missing = [field for field in required if not isinstance(source.get(field), str) or not source[field]]
        if missing:
            raise CandidateValidationError(f"Source record missing required text fields: {missing}")
        if source["source_id"] in known_sources:
            raise CandidateValidationError(f"Duplicate source_id: {source['source_id']}")
        known_sources.add(source["source_id"])

    completeness_path = resolve_inside(root, manifest["completeness"])
    completeness = load_mapping(completeness_path)
    dimensions = completeness.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        raise CandidateValidationError("Completeness dimensions must be non-empty")
    weights = sum(float(item["weight_percent"]) for item in dimensions)
    if abs(weights - 100.0) > 0.000001:
        raise CandidateValidationError("Completeness weights must total 100")
    weighted = sum(float(item["weight_percent"]) * float(item["coverage_percent"]) for item in dimensions) / 100
    completeness["content_completeness_percent"] = round(weighted)
    completeness["trusted_runtime_readiness_percent"] = 0
    scoring = completeness.setdefault("scoring_method", {})
    scoring["method"] = "weighted_dimension_mean_rounded_to_nearest_integer"
    scoring["unrounded_weighted_score"] = round(weighted, 4)
    write_yaml(completeness_path, completeness)

    total_claims = 0
    module_ids: set[str] = set()
    for entry in manifest.get("modules", []):
        module_path = resolve_inside(root, entry["path"])
        module = load_mapping(module_path)
        module_id = module.get("module_id")
        if module_id in module_ids:
            raise CandidateValidationError(f"Duplicate module_id: {module_id}")
        if module.get("approval_state") != "CANDIDATE" or module.get("runtime_eligible") is not False:
            raise CandidateValidationError(f"Module {module_id} must remain CANDIDATE and non-runtime")
        top_sources = set(strings(module.get("source_references", []), f"{module_id}.source_references"))
        nested_sources = set(collect_source_ids(module.get("content", {})))
        unknown = (top_sources | nested_sources) - known_sources
        if unknown:
            raise CandidateValidationError(f"Module {module_id} references unknown sources: {sorted(unknown)}")
        total_claims += validate_claims(module, known_sources)
        entry["sha256"] = sha256(module_path)
        module_ids.add(str(module_id))

    for entry in manifest.get("assets", []):
        asset_path = resolve_inside(root, entry["path"])
        if not asset_path.is_file():
            raise CandidateValidationError(f"Missing declared asset: {entry['path']}")
        entry["sha256"] = sha256(asset_path)
    write_yaml(manifest_path, manifest)

    sys.path.insert(0, str(root / "src"))
    from agentic_data_modeler.knowledge.validation import validate_repository_pack

    validate_repository_pack(root, manifest_relative)
    print(f"validated_manifest={manifest_relative}")
    print(f"modules={len(module_ids)} claims={total_claims} sources={len(known_sources)}")
    print(f"content_completeness_percent={completeness['content_completeness_percent']}")
    print("approval_state=CANDIDATE runtime_eligible=false")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    try:
        validate_and_finalize(args.repository_root, args.manifest)
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

