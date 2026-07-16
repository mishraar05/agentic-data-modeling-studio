"""Reference tests for the Increment-1 contract suite.

Copy into the project test tree and replace example-only helpers with calls to
the production contract validator. Structural validation and dataset-level
referential validation are deliberately separate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

CONTRACTS = Path(__file__).resolve().parents[2] / "contracts"


def _load(name: str) -> dict[str, Any]:
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


def _registry() -> Registry:
    common = _load("_common.schema.json")
    return Registry().with_resource(common["$id"], Resource.from_contents(common))


def _validator(schema_name: str) -> Draft202012Validator:
    return Draft202012Validator(
        _load(f"{schema_name}.schema.json"),
        registry=_registry(),
        format_checker=FormatChecker(),
    )


def _is_valid(schema_name: str, instance: dict[str, Any]) -> bool:
    return not list(_validator(schema_name).iter_errors(instance))


HASH = "a" * 64
ENVELOPE = {
    "record_id": "synthetic-record-1",
    "schema_version": "0.1.0",
    "engagement_id": "synthetic-engagement",
    "lob": "synthetic-lob",
    "domain": "synthetic-domain",
    "artifact_version": "0.1.0",
    "lifecycle_state": "DRAFT",
    "provenance": {
        "work_package_id": "synthetic-work-package",
        "run_id": "synthetic-run",
        "context_snapshot_id": "synthetic-context",
    },
    "created_at": "2026-07-16T00:00:00Z",
    "updated_at": "2026-07-16T00:00:00Z",
}


def _text_claim(state: str = "OBSERVED", **overrides: Any) -> dict[str, Any]:
    claim: dict[str, Any] = {
        "value_type": "TEXT",
        "value": "synthetic meaning",
        "evidence_state": state,
        "evidence_refs": ["synthetic-evidence-1"],
    }
    if state == "INFERRED":
        claim["confidence"] = {
            "evidence_type": "SINGLE_LLM_INFERENCE",
            "evidence_count": 1,
            "critic_agreement": "NOT_ASSESSED",
        }
    claim.update(overrides)
    return claim


def _attribute(**overrides: Any) -> dict[str, Any]:
    record = {
        **ENVELOPE,
        "source_system_id": "synthetic-source",
        "source_attribute_observation_ref": "synthetic-observation-1",
        "schema_name": "synthetic_schema",
        "object_name": "synthetic_object",
        "attribute_name": "synthetic_attribute",
        "ordinal_position": 1,
        "physical": {
            "data_type": "string",
            "nullable": True,
            "evidence_refs": ["synthetic-evidence-1"],
        },
        "business_definition": _text_claim(),
    }
    record.update(overrides)
    return record


def test_structural_positive() -> None:
    assert _is_valid("source_dictionary_attribute", _attribute())


def test_profile_is_optional_for_metadata_only_mode() -> None:
    assert "profile_evidence_ref" not in _attribute()
    assert _is_valid("source_dictionary_attribute", _attribute())


def test_wrong_schema_version_fails() -> None:
    assert not _is_valid("source_dictionary_attribute", _attribute(schema_version="9.9.9"))


def test_extra_property_fails() -> None:
    assert not _is_valid("source_dictionary_attribute", _attribute(unexpected="x"))


def test_physical_without_evidence_fails() -> None:
    assert not _is_valid(
        "source_dictionary_attribute",
        _attribute(physical={"data_type": "string", "nullable": True}),
    )


def test_observed_without_value_fails() -> None:
    claim = {"evidence_state": "OBSERVED", "evidence_refs": ["synthetic-evidence-1"]}
    assert not _is_valid("source_dictionary_attribute", _attribute(business_definition=claim))


def test_list_discriminator_rejects_string() -> None:
    claim = _text_claim(value_type="LIST", value="not-a-list")
    assert not _is_valid("source_dictionary_attribute", _attribute(synonyms=claim))


def test_list_discriminator_accepts_list() -> None:
    claim = _text_claim(value_type="LIST", value=["synthetic-a", "synthetic-b"])
    assert _is_valid("source_dictionary_attribute", _attribute(synonyms=claim))


def test_privacy_class_requires_governed_reference() -> None:
    claim = _text_claim(state="INFERRED", value_type="PRIVACY_CLASS")
    assert not _is_valid("source_dictionary_attribute", _attribute(sensitivity_class=claim))


def test_privacy_class_with_exact_governed_reference_passes() -> None:
    claim = _text_claim(
        state="INFERRED",
        value_type="PRIVACY_CLASS",
        governed_code_ref={
            "pack_id": "synthetic_pack",
            "pack_version": "1.0.0",
            "code_set_id": "synthetic_privacy",
            "fingerprint": HASH,
            "code": "SYNTHETIC_CODE",
        },
    )
    assert _is_valid("source_dictionary_attribute", _attribute(sensitivity_class=claim))


def test_unbounded_mapping_object_fails() -> None:
    claim = _text_claim(value_type="MAPPING", value={"arbitrary": "field"})
    assert not _is_valid("source_dictionary_attribute", _attribute(business_definition=claim))


def test_closed_mapping_value_passes() -> None:
    claim = _text_claim(
        value_type="MAPPING",
        value={"entries": [{"key": "synthetic-key", "value": "synthetic-value"}]},
    )
    assert _is_valid("source_dictionary_attribute", _attribute(business_definition=claim))


def test_inferred_evidence_count_zero_fails() -> None:
    claim = _text_claim(state="INFERRED")
    claim["confidence"]["evidence_count"] = 0
    assert not _is_valid("source_dictionary_attribute", _attribute(business_definition=claim))


def test_unresolved_without_value_passes() -> None:
    claim = {"evidence_state": "UNRESOLVED", "open_question_ref": "synthetic-question-1"}
    assert _is_valid("source_dictionary_attribute", _attribute(business_definition=claim))


def test_unresolved_with_value_fails() -> None:
    claim = {
        "evidence_state": "UNRESOLVED",
        "open_question_ref": "synthetic-question-1",
        "value_type": "TEXT",
        "value": "should not be asserted",
    }
    assert not _is_valid("source_dictionary_attribute", _attribute(business_definition=claim))


def test_material_approval_requires_decision() -> None:
    assert not _is_valid("source_dictionary_attribute", _attribute(lifecycle_state="APPROVED"))
    assert _is_valid(
        "source_dictionary_attribute",
        _attribute(lifecycle_state="APPROVED", review_decision_ref="synthetic-decision-1"),
    )


def _walk(node: Any) -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(node, dict):
        if isinstance(node.get("evidence_state"), str):
            yield "claim", node
        if "physical" in node and isinstance(node["physical"], dict):
            yield "physical", node["physical"]
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def check_referential(
    record: dict[str, Any], evidence_items: dict[str, dict[str, Any]]
) -> list[str]:
    """Reference behavior; production code must validate contracts before this pass."""
    problems: set[str] = set()
    expected_engagement = record.get("engagement_id")
    expected_work_package = record.get("provenance", {}).get("work_package_id")
    for kind, node in _walk(record):
        refs = node.get("evidence_refs", [])
        if kind == "claim" and node.get("evidence_state") not in {"OBSERVED", "INFERRED"}:
            continue
        if kind == "claim" and node.get("evidence_state") == "INFERRED":
            count = node.get("confidence", {}).get("evidence_count")
            if count != len(set(refs)):
                problems.add("evidence_count_mismatch")
        for ref in refs:
            evidence = evidence_items.get(ref)
            if evidence is None:
                problems.add(f"missing:{ref}")
                continue
            if evidence.get("provenance_class") != "SOURCE_FACT" and kind == "physical":
                problems.add(f"not_source_fact:{ref}")
            if node.get("evidence_state") == "OBSERVED" and evidence.get("provenance_class") != "SOURCE_FACT":
                problems.add(f"not_source_fact:{ref}")
            if evidence.get("engagement_id") != expected_engagement:
                problems.add(f"cross_engagement:{ref}")
            if evidence.get("provenance", {}).get("work_package_id") != expected_work_package:
                problems.add(f"cross_work_package:{ref}")
    return sorted(problems)


def _evidence(**overrides: Any) -> dict[str, Any]:
    evidence = {
        "record_id": "synthetic-evidence-1",
        "engagement_id": "synthetic-engagement",
        "provenance_class": "SOURCE_FACT",
        "provenance": {"work_package_id": "synthetic-work-package", "run_id": "synthetic-run"},
    }
    evidence.update(overrides)
    return evidence


def test_referential_positive() -> None:
    assert check_referential(_attribute(), {"synthetic-evidence-1": _evidence()}) == []


def test_referential_dangling_reference_fails() -> None:
    assert check_referential(_attribute(), {}) == ["missing:synthetic-evidence-1"]


def test_referential_wrong_provenance_fails() -> None:
    store = {"synthetic-evidence-1": _evidence(provenance_class="DOCUMENT_CLAIM")}
    assert check_referential(_attribute(), store) == ["not_source_fact:synthetic-evidence-1"]


def test_referential_cross_engagement_fails() -> None:
    store = {"synthetic-evidence-1": _evidence(engagement_id="other-engagement")}
    assert check_referential(_attribute(), store) == ["cross_engagement:synthetic-evidence-1"]


def test_referential_cross_work_package_fails() -> None:
    store = {
        "synthetic-evidence-1": _evidence(
            provenance={"work_package_id": "other-work-package", "run_id": "synthetic-run"}
        )
    }
    assert check_referential(_attribute(), store) == ["cross_work_package:synthetic-evidence-1"]


def test_referential_finds_nested_claims_generically() -> None:
    record = _attribute(
        business_purpose=_text_claim(evidence_refs=["synthetic-evidence-2"])
    )
    assert check_referential(record, {"synthetic-evidence-1": _evidence()}) == [
        "missing:synthetic-evidence-2"
    ]
