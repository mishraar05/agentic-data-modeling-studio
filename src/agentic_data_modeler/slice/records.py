"""Builders that emit contract-valid records. Each validates on construction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import common as C
from .contracts import require_valid


@dataclass(frozen=True, slots=True)
class Scope:
    """Run-rooted LOB/domain boundary carried by every record."""

    lob: str
    domain: str
    run_id: str
    memory_partition: str = "default"
    artifact_version: str = "0.1.0"

    def provenance(self, *, context_snapshot_id: str | None = None, **extra: str) -> dict[str, Any]:
        prov: dict[str, Any] = {"run_id": self.run_id}
        if context_snapshot_id:
            prov["context_snapshot_id"] = context_snapshot_id
        prov.update(extra)
        return prov


# --- semantic + physical claim helpers (contracts/_common.schema.json) ---

def observed_claim(value: Any, value_type: str, evidence_refs: list[str]) -> dict[str, Any]:
    return {"evidence_state": "OBSERVED", "value_type": value_type, "value": value,
            "evidence_refs": sorted(set(evidence_refs))}


def inferred_claim(value: Any, value_type: str, evidence_refs: list[str], confidence: dict) -> dict[str, Any]:
    return {"evidence_state": "INFERRED", "value_type": value_type, "value": value,
            "evidence_refs": sorted(set(evidence_refs)), "confidence": confidence}


def decided_claim(value: Any, value_type: str, review_decision_ref: str) -> dict[str, Any]:
    return {"evidence_state": "DECIDED", "value_type": value_type, "value": value,
            "review_decision_ref": review_decision_ref}


def unresolved_claim(open_question_ref: str) -> dict[str, Any]:
    return {"evidence_state": "UNRESOLVED", "open_question_ref": open_question_ref}


def physical(value: Any, value_type: str, evidence_refs: list[str]) -> dict[str, Any]:
    return {"value": value, "value_type": value_type, "evidence_refs": sorted(set(evidence_refs))}


def confidence(evidence_type: str, evidence_count: int, critic_agreement: str) -> dict[str, Any]:
    return {"evidence_type": evidence_type, "evidence_count": max(1, evidence_count),
            "critic_agreement": critic_agreement}


# --- record builders ---

def context_snapshot(root: Path, scope: Scope, *, evidence_set_ref: str, pack_id: str,
                     pack_version: str, module_ids: list[str], size_bytes: int,
                     fingerprint: str) -> dict[str, Any]:
    rec = C.envelope(
        record_id=C.stable_id("context_snapshot", scope.run_id, fingerprint),
        lob=scope.lob, domain=scope.domain,
        artifact_version=scope.artifact_version, lifecycle_state="COMMITTED",
        provenance=scope.provenance(),
    )
    rec.update({
        "solution_run_ref": scope.run_id,
        "evidence_set_ref": evidence_set_ref,
        "snapshot_timestamp": C.now_iso(),
        "knowledge_pack_id": pack_id,
        "knowledge_pack_version": pack_version,
        "selected_modules": sorted(set(module_ids)),
        "context_effective_date": C.today_iso(),
        "context_size_bytes": max(1, size_bytes),
        "context_fingerprint": fingerprint,
        "budget_compliance": True,
    })
    return require_valid(root, C.C_CONTEXT_SNAPSHOT, rec)


def object_observation(root: Path, scope: Scope, *, snapshot_ref: str, evidence_item_ref: str,
                       catalog: str, schema: str, object_name: str, object_type: str,
                       attribute_count: int) -> dict[str, Any]:
    rec = C.envelope(
        record_id=C.stable_id("source_object_observation", scope.run_id, object_name),
        lob=scope.lob, domain=scope.domain,
        artifact_version=scope.artifact_version, lifecycle_state="COMMITTED",
        provenance=scope.provenance(source_snapshot_id=snapshot_ref),
    )
    rec.update({
        "source_snapshot_ref": snapshot_ref, "evidence_item_ref": evidence_item_ref,
        "catalog_name": catalog, "schema_name": schema, "object_name": object_name,
        "object_type": object_type, "attribute_count": attribute_count,
    })
    return require_valid(root, C.C_OBJECT_OBS, rec)


def attribute_observation(root: Path, scope: Scope, *, snapshot_ref: str, evidence_item_ref: str,
                          object_name: str, attribute_name: str, ordinal: int, data_type: str,
                          nullable: bool, constraint_role: str) -> dict[str, Any]:
    rec = C.envelope(
        record_id=C.stable_id("source_attribute_observation", scope.run_id, object_name, attribute_name),
        lob=scope.lob, domain=scope.domain,
        artifact_version=scope.artifact_version, lifecycle_state="COMMITTED",
        provenance=scope.provenance(source_snapshot_id=snapshot_ref),
    )
    rec.update({
        "source_snapshot_ref": snapshot_ref, "evidence_item_ref": evidence_item_ref,
        "object_name": object_name, "attribute_name": attribute_name, "ordinal_position": ordinal,
        "data_type": data_type, "nullable": nullable, "constraint_role": constraint_role,
    })
    return require_valid(root, C.C_ATTRIBUTE_OBS, rec)


def open_question(root: Path, scope: Scope, *, question_text: str, question_type: str,
                  context_snapshot_ref: str | None = None) -> dict[str, Any]:
    rec = C.envelope(
        record_id=C.stable_id("open_question", scope.run_id, question_text),
        lob=scope.lob, domain=scope.domain,
        artifact_version=scope.artifact_version, lifecycle_state="OPEN",
        provenance=scope.provenance(),
    )
    rec.update({
        "solution_run_ref": scope.run_id,
        "question_text": question_text, "question_type": question_type,
    })
    if context_snapshot_ref:
        rec["context_snapshot_ref"] = context_snapshot_ref
    return require_valid(root, C.C_OPEN_QUESTION, rec)


def review_item(root: Path, scope: Scope, *, artifact_version_ref: str, review_question: str) -> dict[str, Any]:
    rec = C.envelope(
        record_id=C.stable_id("review_item", scope.run_id, artifact_version_ref, review_question),
        lob=scope.lob, domain=scope.domain,
        artifact_version=scope.artifact_version, lifecycle_state="OPEN",
        provenance=scope.provenance(),
    )
    rec.update({"artifact_version_ref": artifact_version_ref, "review_question": review_question})
    return require_valid(root, C.C_REVIEW_ITEM, rec)


def review_decision(root: Path, scope: Scope, *, review_item_ref: str, decision: str,
                    decision_maker: str, rationale: str, impact_scope: list[str] | None = None) -> dict[str, Any]:
    rec = C.envelope(
        record_id=C.stable_id("review_decision", scope.run_id, review_item_ref),
        lob=scope.lob, domain=scope.domain,
        artifact_version=scope.artifact_version, lifecycle_state="RECORDED",
        provenance=scope.provenance(),
    )
    rec.update({
        "review_item_ref": review_item_ref, "decision": decision,
        "decision_maker": decision_maker, "decision_timestamp": C.now_iso(),
        "rationale": rationale,
    })
    if impact_scope:
        rec["impact_scope"] = impact_scope
    return require_valid(root, C.C_REVIEW_DECISION, rec)


def dictionary_attribute(root: Path, scope: Scope, *, context_snapshot_ref: str,
                         attribute_observation_ref: str, object_name: str, attribute_name: str,
                         ordinal: int, data_type: str, nullable: bool,
                         business_name: dict, business_definition: dict,
                         lifecycle_state: str = "DRAFT",
                         key_role: dict | None = None, privacy_class: dict | None = None,
                         open_question_refs: list[str] | None = None,
                         review_decision_ref: str | None = None,
                         notes: str | None = None) -> dict[str, Any]:
    rec = C.envelope(
        record_id=C.stable_id("source_dictionary_attribute", scope.run_id, object_name, attribute_name),
        lob=scope.lob, domain=scope.domain,
        artifact_version=scope.artifact_version, lifecycle_state=lifecycle_state,
        provenance=scope.provenance(context_snapshot_id=context_snapshot_ref),
    )
    rec.update({
        "context_snapshot_ref": context_snapshot_ref,
        "source_attribute_observation_ref": attribute_observation_ref,
        "source_object_name": object_name,
        "source_attribute_name": attribute_name,
        "ordinal_position": ordinal,
        "physical_type": physical(data_type, "TEXT", [attribute_observation_ref]),
        "physical_nullable": physical(nullable, "BOOLEAN", [attribute_observation_ref]),
        "business_name": business_name,
        "business_definition": business_definition,
    })
    if key_role:
        rec["key_role"] = key_role
    if privacy_class:
        rec["privacy_class"] = privacy_class
    if open_question_refs:
        rec["open_question_refs"] = sorted(set(open_question_refs))
    if review_decision_ref:
        rec["review_decision_ref"] = review_decision_ref
    if notes:
        rec["notes"] = notes
    return require_valid(root, C.C_DICT_ATTR, rec)
