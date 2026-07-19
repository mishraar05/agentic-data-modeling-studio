"""Contract-valid record builders the analyst emits beyond attributes.

Reuses the shared envelope/claim helpers; validates on construction (fail-closed).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..slice import common as C
from ..slice.contracts import require_valid
from ..slice.records import Scope

C_DICT_OBJECT = "urn:agentic-data-modeler:contract:source_dictionary_object:0.1.0"
C_VALIDATION_FINDING = "urn:agentic-data-modeler:contract:validation_finding:0.1.0"
C_RELATIONSHIP_CANDIDATE = "urn:agentic-data-modeler:contract:relationship_candidate:0.2.0"


def dictionary_object(root: Path, scope: Scope, *, context_snapshot_ref: str,
                      object_observation_ref: str, evidence_item_ref: str, object_name: str,
                      business_name: dict, business_definition: dict, business_purpose: dict,
                      entity_type: dict, attribute_refs: list[str],
                      lifecycle_state: str = "DRAFT", open_question_refs: list[str] | None = None,
                      review_decision_ref: str | None = None) -> dict[str, Any]:
    rec = C.envelope(
        record_id=C.stable_id("source_dictionary_object", scope.run_id, object_name),
        lob=scope.lob, domain=scope.domain,
        artifact_version=scope.artifact_version, lifecycle_state=lifecycle_state,
        provenance=scope.provenance(context_snapshot_id=context_snapshot_ref))
    rec.update({
        "context_snapshot_ref": context_snapshot_ref,
        "source_object_observation_ref": object_observation_ref,
        "evidence_item_ref": evidence_item_ref,
        "source_object_name": object_name,
        "business_name": business_name,
        "business_definition": business_definition,
        "business_purpose": business_purpose,
        "entity_type": entity_type,
        "attribute_refs": list(attribute_refs),
    })
    if open_question_refs:
        rec["open_question_refs"] = sorted(set(open_question_refs))
    if review_decision_ref:
        rec["review_decision_ref"] = review_decision_ref
    return require_valid(root, C_DICT_OBJECT, rec)


def validation_finding(root: Path, scope: Scope, *, artifact_version_ref: str, finding_type: str,
                       severity: str, finding_text: str, affected_record_refs: list[str] | None = None,
                       evidence_item_ref: str | None = None) -> dict[str, Any]:
    rec = C.envelope(
        record_id=C.stable_id("validation_finding", scope.run_id, artifact_version_ref, finding_text),
        lob=scope.lob, domain=scope.domain,
        artifact_version=scope.artifact_version, lifecycle_state="OPEN",
        provenance=scope.provenance())
    rec.update({
        "artifact_version_ref": artifact_version_ref,
        "finding_type": finding_type,      # SCHEMA | REFERENTIAL | COVERAGE | POLICY | CONTRADICTION
        "severity": severity,              # BLOCKING | ERROR | WARNING | INFO
        "finding_text": finding_text,
    })
    if affected_record_refs:
        rec["affected_record_refs"] = list(affected_record_refs)
    if evidence_item_ref:
        rec["evidence_item_ref"] = evidence_item_ref
    return require_valid(root, C_VALIDATION_FINDING, rec)


def relationship_candidate(
    root: Path,
    scope: Scope,
    *,
    context_snapshot_ref: str,
    source_snapshot_ref: str,
    evidence_set_ref: str,
    parent_object_observation_ref: str,
    child_object_observation_ref: str,
    parent_object_name: str,
    child_object_name: str,
    parent_attributes: list[str],
    child_attributes: list[str],
    relationship_type: str,
    relationship_name: dict,
    cardinality: dict,
    optionality: dict,
    rationale: str,
    evidence_refs: list[str],
    critic_status: str,
    memory_refs: list[str] | None = None,
    open_question_refs: list[str] | None = None,
    lifecycle_state: str = "DRAFT",
    review_decision_ref: str | None = None,
) -> dict[str, Any]:
    rec = C.envelope(
        record_id=C.stable_id(
            "relationship_candidate", context_snapshot_ref,
            parent_object_name, *parent_attributes,
            child_object_name, *child_attributes,
        ),
        lob=scope.lob,
        domain=scope.domain,
        artifact_version=scope.artifact_version,
        lifecycle_state=lifecycle_state,
        provenance=scope.provenance(context_snapshot_id=context_snapshot_ref),
        schema_version="0.2.0",
    )
    rec.update({
        "context_snapshot_ref": context_snapshot_ref,
        "source_snapshot_ref": source_snapshot_ref,
        "evidence_set_ref": evidence_set_ref,
        "parent_object_observation_ref": parent_object_observation_ref,
        "child_object_observation_ref": child_object_observation_ref,
        "parent_object_name": parent_object_name,
        "child_object_name": child_object_name,
        "parent_attributes": list(parent_attributes),
        "child_attributes": list(child_attributes),
        "relationship_type": relationship_type,
        "relationship_name": relationship_name,
        "cardinality": cardinality,
        "optionality": optionality,
        "rationale": rationale,
        "evidence_refs": sorted(set(evidence_refs)),
        "critic_status": critic_status,
    })
    if memory_refs:
        rec["memory_refs"] = sorted(set(memory_refs))
    if open_question_refs:
        rec["open_question_refs"] = sorted(set(open_question_refs))
    if review_decision_ref:
        rec["review_decision_ref"] = review_decision_ref
    return require_valid(root, C_RELATIONSHIP_CANDIDATE, rec)


C_CODE_VALUE = "urn:agentic-data-modeler:contract:source_dictionary_code_value:0.1.0"


def code_value(root: Path, scope: Scope, *, context_snapshot_ref: str, attribute_ref: str,
               evidence_item_ref: str, code: str, meaning: dict, frequency: int | None = None,
               governed_code_ref: dict | None = None, lifecycle_state: str = "DRAFT") -> dict[str, Any]:
    rec = C.envelope(
        record_id=C.stable_id("source_dictionary_code_value", scope.run_id, attribute_ref, code),
        lob=scope.lob, domain=scope.domain, artifact_version=scope.artifact_version,
        lifecycle_state=lifecycle_state, provenance=scope.provenance(context_snapshot_id=context_snapshot_ref))
    rec.update({
        "context_snapshot_ref": context_snapshot_ref, "attribute_ref": attribute_ref,
        "evidence_item_ref": evidence_item_ref, "code": code, "meaning": meaning})
    if frequency is not None:
        rec["frequency"] = int(frequency)
    if governed_code_ref:
        rec["governed_code_ref"] = governed_code_ref
    return require_valid(root, C_CODE_VALUE, rec)
