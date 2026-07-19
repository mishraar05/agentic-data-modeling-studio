"""SA1 producer — Phases 3-4 of the Source Data Analyst.

For each in-scope attribute it asks the model for meaning, then *deterministically*
enforces the trust rules before anything becomes a claim:
  - a value with a valid evidence citation  -> INFERRED (with confidence),
  - a prior human decision                  -> DECIDED (reused, no model call),
  - anything else (no value, no citation, or an invented/again-uncited citation)
                                            -> UNRESOLVED + open_question.
The model can never cause an INFERRED claim without a real citation, and can
never introduce an evidence id outside the allowed set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import records as AR
from ..slice import records as R
from ..slice.records import Scope
from .confidence import derive_confidence, glossary_hit
from .model import AnalystModel, AttributeRequest, FieldProposal, ObjectRequest
from .sa3 import privacy_signal


@dataclass(slots=True)
class AnalystResult:
    dictionary_attributes: list[dict[str, Any]]
    open_questions: list[dict[str, Any]]
    dictionary_objects: list[dict[str, Any]] = field(default_factory=list)
    n_inferred: int = 0
    n_decided: int = 0
    n_unresolved: int = 0
    n_privacy_flagged: int = 0
    n_reused_draft: int = 0
    n_objects_inferred: int = 0
    n_objects_unresolved: int = 0


def _subject_key(memory_partition: str, obj: str, attr: str) -> str:
    return f"{memory_partition}::{obj}::{attr}"


class SourceDataAnalyst:
    """The runtime agent: executes SA1 through a pluggable model, safely."""

    def __init__(self, repo_root: str | Path, model: AnalystModel):
        self.root = Path(repo_root)
        self.model = model

    def analyze_attributes(
        self, scope: Scope, *, context_snapshot_ref: str,
        attribute_observations: list[dict[str, Any]], glossary: dict[str, str] | None = None,
        prior: dict[str, dict[str, Any]] | None = None,
    ) -> AnalystResult:
        glossary = glossary or {}
        prior = prior or {}
        result = AnalystResult(dictionary_attributes=[], open_questions=[])

        for obs in attribute_observations:
            obj, attr, obs_ref = obs["object_name"], obs["attribute_name"], obs["record_id"]
            common = dict(context_snapshot_ref=context_snapshot_ref, attribute_observation_ref=obs_ref,
                          object_name=obj, attribute_name=attr, ordinal=obs["ordinal_position"],
                          data_type=obs["data_type"], nullable=obs["nullable"])

            # --- episodic reuse (Phase 0): approved -> DECIDED; prior AI draft -> carry-forward ---
            prior_entry = prior.get(_subject_key(scope.memory_partition, obj, attr))
            if prior_entry:
                vals = prior_entry["values"]
                if prior_entry.get("kind") == "DRAFT":  # AI's own unverified guess -> INFERRED, still reviewed
                    cf = derive_confidence(evidence_refs=[obs_ref], constraint_role=obs["constraint_role"])
                    rec = R.dictionary_attribute(
                        self.root, scope, **common,
                        business_name=R.inferred_claim(vals["business_name"], "TEXT", [obs_ref], cf),
                        business_definition=R.inferred_claim(vals["business_definition"], "TEXT", [obs_ref], cf),
                        lifecycle_state="DRAFT",
                        notes="Carried forward from a prior unverified AI draft (not human-approved); re-review.")
                    result.n_inferred += 1
                    result.n_reused_draft += 1
                else:  # human-approved decision -> DECIDED (authoritative)
                    rd_ref = prior_entry["review_decision_ref"]
                    rec = R.dictionary_attribute(
                        self.root, scope, **common,
                        business_name=R.decided_claim(vals["business_name"], "TEXT", rd_ref),
                        business_definition=R.decided_claim(vals["business_definition"], "TEXT", rd_ref),
                        lifecycle_state="APPROVED", review_decision_ref=rd_ref)
                    result.n_decided += 1
                result.dictionary_attributes.append(rec)
                continue

            # --- ask the model, then enforce guardrails ---
            allowed = (obs_ref,)
            analysis = self.model.analyze_attribute(AttributeRequest(
                object_name=obj, attribute_name=attr, data_type=obs["data_type"],
                nullable=obs["nullable"], constraint_role=obs["constraint_role"],
                observation_ref=obs_ref, allowed_evidence=allowed, glossary=glossary))

            conf = derive_confidence(evidence_refs=[obs_ref], constraint_role=obs["constraint_role"],
                                     is_glossary_hit=glossary_hit(attr, glossary))
            open_q: dict[str, Any] | None = None

            def resolve(fp: FieldProposal) -> dict[str, Any]:
                nonlocal open_q
                refs = [r for r in fp.evidence_refs if r in allowed]   # strip invented/out-of-scope refs
                if fp.value and refs:
                    return R.inferred_claim(fp.value, "TEXT", refs, conf)
                if open_q is None:
                    open_q = R.open_question(
                        self.root, scope, context_snapshot_ref=context_snapshot_ref,
                        question_text=f"What is the business meaning of {obj}.{attr}? "
                                      f"Model evidence was insufficient or uncited.",
                        question_type="MISSING_EVIDENCE")
                return R.unresolved_claim(open_q["record_id"])

            name_claim = resolve(analysis.business_name)
            def_claim = resolve(analysis.business_definition)

            oq_refs: list[str] = []
            notes: str | None = None
            if open_q is not None:
                oq_refs.append(open_q["record_id"])
                result.open_questions.append(open_q)
                result.n_unresolved += 1
            else:
                result.n_inferred += 1

            # SA3 — privacy signal routes to a steward (candidate only; never a governed class here)
            if privacy_signal(attr, obs["data_type"]):
                pq = R.open_question(
                    self.root, scope, context_snapshot_ref=context_snapshot_ref,
                    question_text=f"Confirm privacy/sensitivity classification for {obj}.{attr}; "
                                  f"candidate sensitive — route to privacy_steward.",
                    question_type="UNCLEAR_REQUIREMENT")
                oq_refs.append(pq["record_id"])
                result.open_questions.append(pq)
                result.n_privacy_flagged += 1
                notes = "Candidate privacy-sensitive; routed to privacy_steward (SA3)."

            rec = R.dictionary_attribute(
                self.root, scope, **common,
                business_name=name_claim, business_definition=def_claim,
                lifecycle_state="DRAFT", open_question_refs=oq_refs or None, notes=notes)
            result.dictionary_attributes.append(rec)

        return result

    def analyze_objects(self, scope: Scope, *, context_snapshot_ref: str,
                        object_observations: list[dict[str, Any]],
                        attribute_refs_by_object: dict[str, list[str]],
                        attribute_names_by_object: dict[str, list[str]] | None = None,
                        glossary: dict[str, str] | None = None) -> AnalystResult:
        """Phase 3 — propose table-level meaning; entity_type stays TEXT/UNRESOLVED
        (no fabricated governed code). Every object gets its attribute_refs."""
        glossary = glossary or {}
        names_by = attribute_names_by_object or {}
        result = AnalystResult(dictionary_attributes=[], open_questions=[])
        for oo in object_observations:
            obj, obs_ref = oo["object_name"], oo["record_id"]
            ev_ref = oo.get("evidence_item_ref") or obs_ref
            attr_refs = attribute_refs_by_object.get(obj) or []
            if not attr_refs:
                continue                       # contract requires >=1 attribute_refs
            allowed = (obs_ref,)
            analysis = self.model.analyze_object(ObjectRequest(
                object_name=obj, object_type=oo.get("object_type", "TABLE"),
                attribute_names=tuple(names_by.get(obj, [])),
                observation_ref=obs_ref, allowed_evidence=allowed, glossary=glossary))
            conf = derive_confidence(evidence_refs=[obs_ref], is_glossary_hit=glossary_hit(obj, glossary))
            open_q: dict[str, Any] | None = None

            def resolve(fp: FieldProposal) -> dict[str, Any]:
                nonlocal open_q
                refs = [r for r in fp.evidence_refs if r in allowed]
                if fp.value and refs:
                    return R.inferred_claim(fp.value, "TEXT", refs, conf)
                if open_q is None:
                    open_q = R.open_question(
                        self.root, scope, context_snapshot_ref=context_snapshot_ref,
                        question_text=f"What is the business meaning of table {obj}? "
                                      f"Model evidence was insufficient or uncited.",
                        question_type="MISSING_EVIDENCE")
                return R.unresolved_claim(open_q["record_id"])

            rec = AR.dictionary_object(
                self.root, scope, context_snapshot_ref=context_snapshot_ref,
                object_observation_ref=obs_ref, evidence_item_ref=ev_ref, object_name=obj,
                business_name=resolve(analysis.business_name),
                business_definition=resolve(analysis.business_definition),
                business_purpose=resolve(analysis.business_purpose),
                entity_type=resolve(analysis.entity_type),
                attribute_refs=attr_refs, lifecycle_state="DRAFT",
                open_question_refs=[open_q["record_id"]] if open_q else None)
            result.dictionary_objects.append(rec)
            if open_q is not None:
                result.open_questions.append(open_q)
                result.n_objects_unresolved += 1
            else:
                result.n_objects_inferred += 1
        return result
