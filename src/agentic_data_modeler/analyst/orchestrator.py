"""Source Data Analyst orchestrator — Phases 3-5 + human review prep.

Ties the pieces into one call: attributes (SA1 + SA3), objects (SA1), the
independent critic (CR1, different model), and review-item preparation for the
human approval gate. Nothing is auto-approved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..slice import records as R
from ..slice.records import Scope
from .confidence import apply_critic_agreement
from .critic import Critic
from .gap_check import run_gap_checks
from .model import AnalystModel, CriticModel
from .review import prepare_review_items
from .sa1 import SourceDataAnalyst
from .sa2 import code_value_records


@dataclass(slots=True)
class SourceDictionaryDraft:
    dictionary_objects: list[dict[str, Any]] = field(default_factory=list)
    dictionary_attributes: list[dict[str, Any]] = field(default_factory=list)
    code_values: list[dict[str, Any]] = field(default_factory=list)
    open_questions: list[dict[str, Any]] = field(default_factory=list)
    validation_findings: list[dict[str, Any]] = field(default_factory=list)
    review_items: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


def analyze_source(
    repo_root: str | Path, scope: Scope, *, context_snapshot_ref: str,
    object_observations: list[dict[str, Any]], attribute_observations: list[dict[str, Any]],
    producer_model: AnalystModel, critic_model: CriticModel | None = None,
    glossary: dict[str, str] | None = None, prior: dict[str, dict[str, Any]] | None = None,
    coded: dict[str, dict[str, Any]] | None = None,
) -> SourceDictionaryDraft:
    root = Path(repo_root)
    analyst = SourceDataAnalyst(root, producer_model)

    # Phase 4 — attributes (SA1 meaning + SA3 privacy routing, episodic reuse)
    attr = analyst.analyze_attributes(
        scope, context_snapshot_ref=context_snapshot_ref,
        attribute_observations=attribute_observations, glossary=glossary, prior=prior)

    refs_by_object: dict[str, list[str]] = {}
    names_by_object: dict[str, list[str]] = {}
    attr_by_key: dict[str, dict[str, Any]] = {}
    for a in attr.dictionary_attributes:
        obj_name, at_name = a["source_object_name"], a["source_attribute_name"]
        refs_by_object.setdefault(obj_name, []).append(a["record_id"])
        names_by_object.setdefault(obj_name, []).append(at_name)
        attr_by_key[f"{obj_name}.{at_name}"] = a

    # Phase 3 — objects (needs the attribute refs)
    obj = analyst.analyze_objects(
        scope, context_snapshot_ref=context_snapshot_ref, object_observations=object_observations,
        attribute_refs_by_object=refs_by_object, attribute_names_by_object=names_by_object,
        glossary=glossary)

    # Phase 4b — SA2 code values (only where a distribution + governed code set are supplied)
    code_values: list[dict[str, Any]] = []
    sa2_unmapped = 0
    for key, spec in (coded or {}).items():
        a = attr_by_key.get(key)
        if not a:
            continue
        recs, unmapped = code_value_records(
            root, scope, context_snapshot_ref=context_snapshot_ref, attribute_ref=a["record_id"],
            evidence_item_ref=a["source_attribute_observation_ref"],
            distribution=spec["distribution"], code_set=spec["code_set"])
        code_values.extend(recs)
        if unmapped:
            sa2_unmapped += len(unmapped)
            attr.open_questions.append(R.open_question(
                root, scope, context_snapshot_ref=context_snapshot_ref,
                question_text=f"{len(unmapped)} value(s) of {key} have no governed code: "
                              f"{sorted(unmapped)[:10]}.",
                question_type="MISSING_EVIDENCE"))

    # Phase 5a — deterministic gap/contradiction checks (code, cannot be missed)
    gap_findings = run_gap_checks(
        root, scope, artifact_version_ref=context_snapshot_ref,
        dictionary_attributes=attr.dictionary_attributes,
        attribute_observations=attribute_observations,
        dictionary_objects=obj.dictionary_objects, glossary=glossary)

    # Phase 5b — independent LLM critic (separate model); record agreement into confidence (Phase 6)
    critic_findings: list[dict[str, Any]] = []
    if critic_model is not None:
        critic_findings = Critic(root, critic_model).review(
            scope, artifact_version_ref=context_snapshot_ref,
            dictionary_attributes=attr.dictionary_attributes,
            dictionary_objects=obj.dictionary_objects)
        apply_critic_agreement(attr.dictionary_attributes, critic_findings,
                               claim_fields=["business_name", "business_definition"])
        apply_critic_agreement(obj.dictionary_objects, critic_findings,
                               claim_fields=["business_name", "business_definition",
                                             "business_purpose", "entity_type"])
    findings = gap_findings + critic_findings

    # Phase 8 prep — human review items (no auto-approve)
    review_items = prepare_review_items(
        root, scope, dictionary_objects=obj.dictionary_objects,
        dictionary_attributes=attr.dictionary_attributes, validation_findings=findings)

    return SourceDictionaryDraft(
        dictionary_objects=obj.dictionary_objects,
        dictionary_attributes=attr.dictionary_attributes, code_values=code_values,
        open_questions=attr.open_questions + obj.open_questions,
        validation_findings=findings, review_items=review_items,
        stats={
            "attributes": len(attr.dictionary_attributes),
            "attr_inferred": attr.n_inferred, "attr_decided": attr.n_decided,
            "attr_unresolved": attr.n_unresolved, "privacy_flagged": attr.n_privacy_flagged,
            "reused_draft": attr.n_reused_draft,
            "objects": len(obj.dictionary_objects),
            "obj_inferred": obj.n_objects_inferred, "obj_unresolved": obj.n_objects_unresolved,
            "code_values": len(code_values), "code_unmapped": sa2_unmapped,
            "gap_findings": len(gap_findings), "critic_findings": len(critic_findings),
            "findings": len(findings), "review_items": len(review_items),
            "open_questions": len(attr.open_questions) + len(obj.open_questions),
        })
