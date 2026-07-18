"""Source Data Analyst producer (Phases 3-4).

For each attribute it either:
  - reuses a prior human decision from episodic memory  -> DECIDED claim (no LLM), or
  - asks the pluggable LLM for meaning                  -> INFERRED claim (cites evidence), or
  - finds the column opaque                             -> UNRESOLVED + open_question (never guess).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import records
from .context import ContextEnvelope
from .llm import LLM
from .memory import EpisodicMemory, subject_key
from .records import Scope


@dataclass(slots=True)
class ProducedAttribute:
    draft: dict[str, Any]
    subject_key: str
    resolved: bool
    from_memory: bool
    approved_values: dict[str, Any] = field(default_factory=dict)
    open_question: dict[str, Any] | None = None


def analyze_attributes(root: Path, scope: Scope, ctx: ContextEnvelope,
                       attribute_observations: list[dict[str, Any]], *,
                       memory: EpisodicMemory, llm: LLM) -> list[ProducedAttribute]:
    produced: list[ProducedAttribute] = []
    for obs in attribute_observations:
        obj, attr = obs["object_name"], obs["attribute_name"]
        obs_ref, ordinal = obs["record_id"], obs["ordinal_position"]
        key = subject_key(scope.engagement_id, obj, attr)

        # --- memory read-back: don't re-litigate what a human already decided ---
        prior = memory.prior_decision(key)
        if prior:
            payload, rd_ref = prior["payload"], prior["record"]["record_id"]
            draft = records.dictionary_attribute(
                root, scope, context_snapshot_ref=ctx.snapshot_id,
                attribute_observation_ref=obs_ref, object_name=obj, attribute_name=attr,
                ordinal=ordinal, data_type=obs["data_type"], nullable=obs["nullable"],
                business_name=records.decided_claim(payload["business_name"], "TEXT", rd_ref),
                business_definition=records.decided_claim(payload["business_definition"], "TEXT", rd_ref),
                lifecycle_state="APPROVED", review_decision_ref=rd_ref,
            )
            produced.append(ProducedAttribute(draft, key, resolved=True, from_memory=True,
                                              approved_values=payload))
            continue

        proposal = llm.propose_attribute(
            object_name=obj, attribute_name=attr, data_type=obs["data_type"],
            nullable=obs["nullable"], constraint_role=obs["constraint_role"],
            glossary_terms=ctx.glossary,
        )

        # --- opaque column: ask, never guess ---
        if not proposal.sufficient:
            oq = records.open_question(
                root, scope, context_snapshot_ref=ctx.snapshot_id,
                question_text=f"What is the business meaning of {obj}.{attr}? The column name is opaque.",
                question_type="AMBIGUOUS_MEANING",
            )
            draft = records.dictionary_attribute(
                root, scope, context_snapshot_ref=ctx.snapshot_id,
                attribute_observation_ref=obs_ref, object_name=obj, attribute_name=attr,
                ordinal=ordinal, data_type=obs["data_type"], nullable=obs["nullable"],
                business_name=records.unresolved_claim(oq["record_id"]),
                business_definition=records.unresolved_claim(oq["record_id"]),
                open_question_refs=[oq["record_id"]], lifecycle_state="DRAFT",
            )
            produced.append(ProducedAttribute(draft, key, resolved=False, from_memory=False,
                                              open_question=oq))
            continue

        # --- sufficient: INFERRED, citing the observation as evidence ---
        conf = records.confidence(
            "GLOSSARY_MATCH" if proposal.glossary_hits else "SINGLE_LLM_INFERENCE",
            1 + len(proposal.glossary_hits), "NOT_ASSESSED",
        )
        notes = "Candidate privacy-sensitive; requires steward confirmation." if proposal.privacy_sensitive else None
        draft = records.dictionary_attribute(
            root, scope, context_snapshot_ref=ctx.snapshot_id,
            attribute_observation_ref=obs_ref, object_name=obj, attribute_name=attr,
            ordinal=ordinal, data_type=obs["data_type"], nullable=obs["nullable"],
            business_name=records.inferred_claim(proposal.business_name, "TEXT", [obs_ref], conf),
            business_definition=records.inferred_claim(proposal.business_definition, "TEXT", [obs_ref], conf),
            lifecycle_state="DRAFT", notes=notes,
        )
        produced.append(ProducedAttribute(
            draft, key, resolved=True, from_memory=False,
            approved_values={"business_name": proposal.business_name,
                             "business_definition": proposal.business_definition},
        ))
    return produced
