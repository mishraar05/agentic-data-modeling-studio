#!/usr/bin/env python3
"""Validate a build-source-discovery-foundation evidence handoff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


EXPECTED_WORK_PACKAGES = {f"I23-{index:02d}" for index in range(9)}
WORK_PACKAGE_STATES = {"NOT_STARTED", "BLOCKED", "BUILT", "VERIFIED"}
BUILD_MODES = {"ALIGNMENT_ONLY", "PHASE_A", "PHASE_B", "FULL_FOUNDATION"}
BUILD_STATES = {"DRAFT", "PARTIAL", "BLOCKED", "COMPLETE"}
BUNDLE_STATES = {"NOT_RUN", "PASS", "FAIL", "BLOCKED"}
REVIEW_STATES = {"PENDING", "ACCEPTED", "REJECTED", "NEEDS_REVISION"}
FORBIDDEN_KEY_FRAGMENTS = ("password", "secret", "token", "credential")
MODE_WORK_PACKAGES = {
    "ALIGNMENT_ONLY": {"I23-00"},
    "PHASE_A": {f"I23-{index:02d}" for index in range(6)},
    "PHASE_B": {"I23-00", "I23-06", "I23-07", "I23-08"},
    "FULL_FOUNDATION": EXPECTED_WORK_PACKAGES,
}


def require_mapping(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be a mapping")
        return {}
    return value


def require_list(value: Any, path: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    return value


def require_value(mapping: dict[str, Any], key: str, path: str, errors: list[str]) -> Any:
    value = mapping.get(key)
    if value is None or value == "":
        errors.append(f"{path}.{key} is required")
    return value


def scan_forbidden_keys(node: Any, path: str, errors: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS):
                errors.append(f"{path}.{key} is a prohibited secret-bearing field")
            scan_forbidden_keys(value, f"{path}.{key}", errors)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            scan_forbidden_keys(value, f"{path}[{index}]", errors)


def scan_placeholders(node: Any, path: str, errors: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            scan_placeholders(value, f"{path}.{key}", errors)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            scan_placeholders(value, f"{path}[{index}]", errors)
    elif isinstance(node, str) and node.startswith("REQUIRED_"):
        errors.append(f"{path} contains unresolved placeholder {node!r}")


def validate(document: Any, *, allow_placeholders: bool = False) -> list[str]:
    errors: list[str] = []
    root = require_mapping(document, "$", errors)
    if not root:
        return errors

    if root.get("schema_version") != "1.0":
        errors.append("$.schema_version must equal '1.0'")

    skill = require_mapping(root.get("skill"), "$.skill", errors)
    if skill.get("name") != "build-source-discovery-foundation":
        errors.append("$.skill.name must equal 'build-source-discovery-foundation'")
    require_value(skill, "version", "$.skill", errors)

    build = require_mapping(root.get("build"), "$.build", errors)
    require_value(build, "build_id", "$.build", errors)
    require_value(build, "contract_set_version", "$.build", errors)
    require_value(build, "target", "$.build", errors)
    require_value(build, "started_at", "$.build", errors)
    if build.get("mode") not in BUILD_MODES:
        errors.append(f"$.build.mode must be one of {sorted(BUILD_MODES)}")
    if build.get("status") not in BUILD_STATES:
        errors.append(f"$.build.status must be one of {sorted(BUILD_STATES)}")

    governance = require_mapping(root.get("governance"), "$.governance", errors)
    decisions = require_list(
        governance.get("authorized_decision_refs"),
        "$.governance.authorized_decision_refs",
        errors,
    )
    for field in (
        "real_source_used",
        "positive_project_knowledge_path_used",
        "mutated_governing_documents",
        "mutated_approval_state",
        "mutated_runtime_eligibility",
    ):
        if not isinstance(governance.get(field), bool):
            errors.append(f"$.governance.{field} must be boolean")
    for field in (
        "mutated_governing_documents",
        "mutated_approval_state",
        "mutated_runtime_eligibility",
    ):
        if governance.get(field) is True:
            errors.append(f"$.governance.{field} must remain false")
    if governance.get("real_source_used") is True:
        for required in ("D23-01", "D23-02"):
            if required not in decisions:
                errors.append(f"real source use requires {required}")
    if governance.get("positive_project_knowledge_path_used") is True and "D23-07" not in decisions:
        errors.append("positive project knowledge path requires D23-07")

    bundle = require_mapping(root.get("bundle_validation"), "$.bundle_validation", errors)
    if bundle.get("status") not in BUNDLE_STATES:
        errors.append(f"$.bundle_validation.status must be one of {sorted(BUNDLE_STATES)}")
    require_value(bundle, "target", "$.bundle_validation", errors)

    packages = require_list(root.get("work_packages"), "$.work_packages", errors)
    seen: set[str] = set()
    package_states: dict[str, str] = {}
    for index, raw_package in enumerate(packages):
        path = f"$.work_packages[{index}]"
        package = require_mapping(raw_package, path, errors)
        package_id = package.get("id")
        if package_id in seen:
            errors.append(f"{path}.id duplicates {package_id}")
        if isinstance(package_id, str):
            seen.add(package_id)
        state = package.get("status")
        if state not in WORK_PACKAGE_STATES:
            errors.append(f"{path}.status must be one of {sorted(WORK_PACKAGE_STATES)}")
        if isinstance(package_id, str) and isinstance(state, str):
            package_states[package_id] = state
        contract_refs = require_list(package.get("contract_refs"), f"{path}.contract_refs", errors)
        files = require_list(package.get("files_changed"), f"{path}.files_changed", errors)
        tests = require_list(package.get("tests"), f"{path}.tests", errors)
        require_list(package.get("decision_refs"), f"{path}.decision_refs", errors)
        blockers = require_list(package.get("blockers"), f"{path}.blockers", errors)
        if state == "VERIFIED":
            if not contract_refs:
                errors.append(f"{path}: VERIFIED requires contract_refs")
            if not files:
                errors.append(f"{path}: VERIFIED requires files_changed")
            if not tests:
                errors.append(f"{path}: VERIFIED requires tests")
        if state == "BLOCKED" and not blockers:
            errors.append(f"{path}: BLOCKED requires blockers")

    missing = EXPECTED_WORK_PACKAGES - seen
    unexpected = seen - EXPECTED_WORK_PACKAGES
    if missing:
        errors.append(f"$.work_packages missing {sorted(missing)}")
    if unexpected:
        errors.append(f"$.work_packages has unexpected IDs {sorted(unexpected)}")

    if build.get("status") == "COMPLETE":
        required_packages = MODE_WORK_PACKAGES.get(build.get("mode"), EXPECTED_WORK_PACKAGES)
        unverified = sorted(
            package_id
            for package_id in required_packages
            if package_states.get(package_id) != "VERIFIED"
        )
        if unverified:
            errors.append(f"COMPLETE build has unverified work packages {unverified}")
        if bundle.get("status") != "PASS":
            errors.append("COMPLETE build requires bundle_validation.status PASS")
        if not bundle.get("evidence_ref"):
            errors.append("COMPLETE build requires bundle_validation.evidence_ref")

    review = require_mapping(root.get("review"), "$.review", errors)
    for field in ("contract_review_state", "architecture_review_state"):
        if review.get(field) not in REVIEW_STATES:
            errors.append(f"$.review.{field} must be one of {sorted(REVIEW_STATES)}")
    require_list(review.get("reviewer_refs"), "$.review.reviewer_refs", errors)
    require_list(root.get("blocking_findings"), "$.blocking_findings", errors)

    scan_forbidden_keys(root, "$", errors)
    if not allow_placeholders:
        scan_placeholders(root, "$", errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handoff", type=Path)
    parser.add_argument(
        "--allow-template",
        action="store_true",
        help="Allow REQUIRED_* placeholders when validating the packaged template.",
    )
    args = parser.parse_args()
    try:
        document = yaml.safe_load(args.handoff.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: unable to read handoff: {exc}", file=sys.stderr)
        return 2
    errors = validate(document, allow_placeholders=args.allow_template)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Builder handoff is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
