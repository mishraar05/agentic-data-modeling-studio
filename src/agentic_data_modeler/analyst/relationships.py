"""LLM-driven source relationship analysis with bounded context and memory.

The model performs semantic discovery. Code only assembles authorized facts,
checks citations/references, applies lifecycle policy, and validates contracts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from ..slice import records as R
from ..slice.records import Scope
from . import records as AR
from .model import (
    AnalystModel,
    CriticModel,
    CritiqueRequest,
    RelationshipProposal,
    RelationshipRequest,
)


_RELATIONSHIP_TYPES = {"FOREIGN_KEY", "INFERRED_FK", "LOOKUP", "BRIDGE", "SELF_REFERENCE"}


@dataclass(frozen=True, slots=True)
class RelationshipContext:
    lob: str
    domain: str
    source_snapshot_ref: str
    evidence_set_ref: str
    context_snapshot_ref: str
    schema_inventory: tuple[dict[str, Any], ...]
    allowed_evidence: tuple[str, ...]
    glossary: dict[str, str] = field(default_factory=dict)
    prior_decisions: tuple[dict[str, Any], ...] = ()

    def request(self) -> RelationshipRequest:
        return RelationshipRequest(
            lob=self.lob,
            domain=self.domain,
            source_snapshot_ref=self.source_snapshot_ref,
            evidence_set_ref=self.evidence_set_ref,
            context_snapshot_ref=self.context_snapshot_ref,
            schema_inventory=self.schema_inventory,
            allowed_evidence=self.allowed_evidence,
            glossary=self.glossary,
            prior_decisions=self.prior_decisions,
        )


@dataclass(slots=True)
class RelationshipDraft:
    candidates: list[dict[str, Any]] = field(default_factory=list)
    open_questions: list[dict[str, Any]] = field(default_factory=list)
    validation_findings: list[dict[str, Any]] = field(default_factory=list)
    review_items: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


def assemble_relationship_context(
    *,
    lob: str,
    domain: str,
    source_snapshot_ref: str,
    evidence_set_ref: str,
    context_snapshot_ref: str,
    object_observations: Iterable[dict[str, Any]],
    attribute_observations: Iterable[dict[str, Any]],
    profile_evidence: Iterable[dict[str, Any]] = (),
    glossary: dict[str, str] | None = None,
    prior_decisions: Iterable[dict[str, Any]] = (),
    max_objects: int = 500,
    max_attributes: int = 5000,
    max_context_bytes: int = 1_500_000,
) -> RelationshipContext:
    """Create the exact model context; fail instead of silently truncating it."""

    objects = [dict(row) for row in object_observations]
    attributes = [dict(row) for row in attribute_observations]
    profiles = [dict(row) for row in profile_evidence]
    if not objects or not attributes:
        raise ValueError("Relationship context requires object and attribute observations")
    if len(objects) > max_objects or len(attributes) > max_attributes:
        raise ValueError(
            f"Relationship context exceeds budget: objects={len(objects)}, attributes={len(attributes)}"
        )

    for row in objects + attributes:
        if row.get("source_snapshot_ref") != source_snapshot_ref:
            raise ValueError("Relationship context mixes source snapshots")

    attrs_by_object: dict[str, list[dict[str, Any]]] = {}
    for row in attributes:
        attrs_by_object.setdefault(str(row["object_name"]), []).append(row)
    profiles_by_key = {
        (str(row["object_name"]), str(row["attribute_name"])): row for row in profiles
    }

    allowed: set[str] = set()
    inventory: list[dict[str, Any]] = []
    for obj in sorted(objects, key=lambda item: str(item["object_name"])):
        object_name = str(obj["object_name"])
        obj_ref = str(obj["record_id"])
        allowed.add(obj_ref)
        if obj.get("evidence_item_ref"):
            allowed.add(str(obj["evidence_item_ref"]))
        rendered_attributes: list[dict[str, Any]] = []
        for attr in sorted(attrs_by_object.get(object_name, []), key=lambda item: int(item["ordinal_position"])):
            attr_ref = str(attr["record_id"])
            allowed.add(attr_ref)
            if attr.get("evidence_item_ref"):
                allowed.add(str(attr["evidence_item_ref"]))
            profile = profiles_by_key.get((object_name, str(attr["attribute_name"])))
            profile_summary = None
            if profile:
                allowed.add(str(profile["record_id"]))
                if profile.get("evidence_item_ref"):
                    allowed.add(str(profile["evidence_item_ref"]))
                profile_summary = {
                    "profile_ref": profile["record_id"],
                    "row_count": profile.get("row_count"),
                    "null_count": profile.get("null_count"),
                    "distinct_count": profile.get("distinct_count"),
                }
            rendered_attributes.append({
                "observation_ref": attr_ref,
                "evidence_item_ref": attr.get("evidence_item_ref"),
                "name": attr["attribute_name"],
                "data_type": attr["data_type"],
                "nullable": attr["nullable"],
                "constraint_role": attr["constraint_role"],
                "profile": profile_summary,
            })
        inventory.append({
            "observation_ref": obj_ref,
            "evidence_item_ref": obj.get("evidence_item_ref"),
            "name": object_name,
            "object_type": obj["object_type"],
            "declared_constraints": obj.get("constraint_observations", []),
            "attributes": rendered_attributes,
        })

    context = RelationshipContext(
        lob=lob,
        domain=domain,
        source_snapshot_ref=source_snapshot_ref,
        evidence_set_ref=evidence_set_ref,
        context_snapshot_ref=context_snapshot_ref,
        schema_inventory=tuple(inventory),
        allowed_evidence=tuple(sorted(allowed)),
        glossary=dict(glossary or {}),
        prior_decisions=tuple(dict(row) for row in prior_decisions),
    )
    payload_size = len(json.dumps({
        "schema_inventory": context.schema_inventory,
        "allowed_evidence": context.allowed_evidence,
        "glossary": context.glossary,
        "prior_decisions": context.prior_decisions,
    }, sort_keys=True, default=str).encode("utf-8"))
    if payload_size > max_context_bytes:
        raise ValueError(
            f"Relationship context exceeds byte budget: {payload_size}>{max_context_bytes}"
        )
    return context


class RelationshipAgent:
    """Producer + independent critic + contract gate for relationship drafts."""

    def __init__(self, repo_root: str | Path, producer: AnalystModel,
                 critic: CriticModel | None = None):
        self.root = Path(repo_root)
        self.producer = producer
        self.critic = critic

    def analyze(self, scope: Scope, context: RelationshipContext) -> RelationshipDraft:
        analysis = self.producer.analyze_relationships(context.request())
        proposals = list(analysis.proposals)

        valid: list[RelationshipProposal] = []
        rejected: list[tuple[RelationshipProposal, str]] = []
        for proposal in proposals:
            error = _validate_proposal(proposal, context)
            if error:
                rejected.append((proposal, error))
            else:
                valid.append(proposal)

        critic_findings = []
        if self.critic is not None and valid:
            critic_findings = self.critic.critique(CritiqueRequest(
                draft_summary=json.dumps([_proposal_payload(p) for p in valid], sort_keys=True),
                evidence_summary=json.dumps(context.schema_inventory, sort_keys=True, default=str),
            ))
        critic_status = "CONTESTED" if critic_findings else (
            "CONFIRMED" if self.critic is not None else "NOT_ASSESSED"
        )

        result = RelationshipDraft()
        for proposal, error in rejected:
            result.validation_findings.append(AR.validation_finding(
                self.root, scope, artifact_version_ref=context.context_snapshot_ref,
                finding_type="REFERENTIAL", severity="ERROR",
                finding_text=f"Rejected relationship proposal: {error}",
                affected_record_refs=list(proposal.evidence_refs),
            ))
        for finding in critic_findings:
            result.validation_findings.append(AR.validation_finding(
                self.root, scope, artifact_version_ref=context.context_snapshot_ref,
                finding_type=finding.finding_type, severity=finding.severity,
                finding_text=finding.finding_text,
                affected_record_refs=list(finding.affected_refs),
            ))

        object_refs = {str(o["name"]): str(o["observation_ref"]) for o in context.schema_inventory}
        memory_by_key = {_memory_key(m): m for m in context.prior_decisions if _memory_key(m)}
        for proposal in valid:
            key = _proposal_key(proposal)
            memory = memory_by_key.get(key)
            question_refs: list[str] = []
            if proposal.open_question or not all((proposal.relationship_name, proposal.cardinality, proposal.optionality)):
                question = R.open_question(
                    self.root, scope,
                    question_text=proposal.open_question or (
                        f"Confirm relationship semantics for {proposal.parent_object} and {proposal.child_object}."
                    ),
                    question_type="RELATIONSHIP",
                    context_snapshot_ref=context.context_snapshot_ref,
                )
                result.open_questions.append(question)
                question_refs.append(question["record_id"])

            if memory:
                decision_ref = str(memory["review_decision_ref"])
                name_claim = R.decided_claim(str(memory["relationship_name"]), "TEXT", decision_ref)
                cardinality_claim = R.decided_claim(str(memory["cardinality"]), "TEXT", decision_ref)
                optionality_claim = R.decided_claim(str(memory["optionality"]), "TEXT", decision_ref)
                lifecycle, memory_refs = "APPROVED", [decision_ref]
            else:
                confidence = R.confidence("SINGLE_LLM_INFERENCE", len(proposal.evidence_refs), critic_status)
                name_claim = _inferred_or_unresolved(proposal.relationship_name, proposal.evidence_refs, confidence, question_refs)
                cardinality_claim = _inferred_or_unresolved(proposal.cardinality, proposal.evidence_refs, confidence, question_refs)
                optionality_claim = _inferred_or_unresolved(proposal.optionality, proposal.evidence_refs, confidence, question_refs)
                decision_ref, lifecycle, memory_refs = None, "DRAFT", []

            candidate = AR.relationship_candidate(
                self.root, scope,
                context_snapshot_ref=context.context_snapshot_ref,
                source_snapshot_ref=context.source_snapshot_ref,
                evidence_set_ref=context.evidence_set_ref,
                parent_object_observation_ref=object_refs[proposal.parent_object],
                child_object_observation_ref=object_refs[proposal.child_object],
                parent_object_name=proposal.parent_object,
                child_object_name=proposal.child_object,
                parent_attributes=list(proposal.parent_attributes),
                child_attributes=list(proposal.child_attributes),
                relationship_type=proposal.relationship_type,
                relationship_name=name_claim,
                cardinality=cardinality_claim,
                optionality=optionality_claim,
                rationale=proposal.rationale,
                evidence_refs=list(proposal.evidence_refs),
                critic_status=critic_status,
                memory_refs=memory_refs,
                open_question_refs=question_refs,
                lifecycle_state=lifecycle,
                review_decision_ref=decision_ref,
            )
            result.candidates.append(candidate)
            if lifecycle != "APPROVED":
                result.review_items.append(R.review_item(
                    self.root, scope, artifact_version_ref=candidate["record_id"],
                    review_question=(
                        f"Review relationship {proposal.child_object}.{','.join(proposal.child_attributes)} "
                        f"to {proposal.parent_object}.{','.join(proposal.parent_attributes)}."
                    ),
                ))

        result.stats = {
            "proposed": len(analysis.proposals),
            "memory_reused": sum(1 for p in valid if _proposal_key(p) in memory_by_key),
            "candidates": len(result.candidates),
            "rejected": len(rejected),
            "critic_findings": len(critic_findings),
            "open_questions": len(result.open_questions),
            "review_items": len(result.review_items),
        }
        return result


def _validate_proposal(proposal: RelationshipProposal, context: RelationshipContext) -> str | None:
    objects = {str(o["name"]): o for o in context.schema_inventory}
    if proposal.parent_object not in objects or proposal.child_object not in objects:
        return "model referenced an object outside the context"
    columns = {
        name: {str(a["name"]) for a in obj["attributes"]} for name, obj in objects.items()
    }
    if not proposal.parent_attributes or not set(proposal.parent_attributes) <= columns[proposal.parent_object]:
        return "parent attributes are missing or outside the context"
    if not proposal.child_attributes or not set(proposal.child_attributes) <= columns[proposal.child_object]:
        return "child attributes are missing or outside the context"
    if len(proposal.parent_attributes) != len(proposal.child_attributes):
        return "parent and child attribute counts differ"
    if proposal.relationship_type not in _RELATIONSHIP_TYPES:
        return "relationship type is not contract-owned"
    if not proposal.rationale:
        return "rationale is empty"
    if not proposal.evidence_refs or not set(proposal.evidence_refs) <= set(context.allowed_evidence):
        return "evidence citations are empty or outside ALLOWED_EVIDENCE"
    return None


def _inferred_or_unresolved(value: str | None, evidence: tuple[str, ...], confidence: dict,
                            question_refs: list[str]) -> dict[str, Any]:
    if value:
        return R.inferred_claim(value, "TEXT", list(evidence), confidence)
    if not question_refs:
        raise ValueError("Unresolved relationship field requires an open question")
    return R.unresolved_claim(question_refs[0])


def _proposal_key(proposal: RelationshipProposal) -> tuple[Any, ...]:
    return (
        proposal.parent_object, tuple(proposal.parent_attributes),
        proposal.child_object, tuple(proposal.child_attributes),
    )


def _memory_key(memory: dict[str, Any]) -> tuple[Any, ...] | None:
    required = ("parent_object", "parent_attributes", "child_object", "child_attributes")
    if not all(memory.get(k) for k in required):
        return None
    return (
        str(memory["parent_object"]), tuple(str(v) for v in memory["parent_attributes"]),
        str(memory["child_object"]), tuple(str(v) for v in memory["child_attributes"]),
    )


def _proposal_payload(proposal: RelationshipProposal) -> dict[str, Any]:
    return {
        "parent_object": proposal.parent_object,
        "parent_attributes": proposal.parent_attributes,
        "child_object": proposal.child_object,
        "child_attributes": proposal.child_attributes,
        "relationship_type": proposal.relationship_type,
        "relationship_name": proposal.relationship_name,
        "cardinality": proposal.cardinality,
        "optionality": proposal.optionality,
        "rationale": proposal.rationale,
        "evidence_refs": proposal.evidence_refs,
        "open_question": proposal.open_question,
    }
