"""run_sdd_agent — Phases 0-9 end to end over an allow-listed source slice.

LEGACY / DEMO PATH. This vertical-slice orchestrator (with its stub LLM,
AutoApprove policy and local JSON stores) exists to demonstrate the flow offline.
The CANONICAL production agent is ``agentic_data_modeler.analyst.analyze_source``
(real model port, independent critic, deterministic gap checks, human review).
Do not extend this module for production; use the analyst package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..evidence.metadata import MetadataInventory
from ..knowledge.registry import select_approved_pack
from . import common as C
from . import records
from .context import assemble_context
from .contracts import require_valid
from .llm import LLM
from .memory import EpisodicMemory, subject_key
from .records import Scope
from .review import ReviewPolicy
from .source_analyst import analyze_attributes


@dataclass(slots=True)
class RunResult:
    run_id: str
    context_snapshot_id: str
    n_attributes: int
    n_approved: int
    n_deferred_unresolved: int
    n_reused_from_memory: int
    open_questions: list[str] = field(default_factory=list)
    table_counts: dict[str, int] = field(default_factory=dict)


def _ingest_evidence(root: Path, scope: Scope, inventory: MetadataInventory, snapshot_ref: str):
    obj_obs, attr_obs = [], []
    for om in sorted(inventory.objects, key=lambda o: o.name):
        ev_item = C.stable_id("evidence_item", scope.run_id, om.name)
        obj_obs.append(records.object_observation(
            root, scope, snapshot_ref=snapshot_ref, evidence_item_ref=ev_item,
            catalog=inventory.catalog, schema=inventory.schema, object_name=om.name,
            object_type=om.object_type, attribute_count=len(om.columns)))
        for col in sorted(om.columns, key=lambda c: c.ordinal_position):
            attr_obs.append(records.attribute_observation(
                root, scope, snapshot_ref=snapshot_ref, evidence_item_ref=ev_item,
                object_name=om.name, attribute_name=col.name, ordinal=col.ordinal_position,
                data_type=col.data_type, nullable=col.nullable,
                constraint_role=col.constraint_role()))
    return obj_obs, attr_obs


def run_sdd_agent(root: Path, scope: Scope, inventory: MetadataInventory, *,
                  memory: EpisodicMemory, store, review_policy: ReviewPolicy, llm: LLM,
                  pack_id: str = "public_us_pnc_personal_auto", pack_version: str = "0.6.0",
                  geography: str = "US_general",
                  pack_domains: set[str] | None = None) -> RunResult:
    root = Path(root)
    pack_domains = pack_domains or {"policy", "claims"}

    # ---- Phase 0: scope + fail-closed pack selection + context assembly ----
    inventory.validate()  # allow-listed, unique, well-formed
    manifest = select_approved_pack(
        root, pack_id=pack_id, pack_version=pack_version,
        geography=geography, lob=scope.lob, domains=pack_domains)
    snapshot_ref = inventory.snapshot_id(scope.run_id)
    ctx = assemble_context(root, scope, manifest=manifest, evidence_set_ref=snapshot_ref,
                           evidence_fingerprint=inventory.fingerprint())
    store.append("context_snapshot", ctx.snapshot)

    # ---- Phase 1: evidence (deterministic facts) ----
    obj_obs, attr_obs = _ingest_evidence(root, scope, inventory, snapshot_ref)
    store.extend("source_object_observation", obj_obs)
    store.extend("source_attribute_observation", attr_obs)

    # ---- Phases 3-4: semantic producer (with episodic read-back) ----
    produced = analyze_attributes(root, scope, ctx, attr_obs, memory=memory, llm=llm)
    for p in produced:
        if p.open_question:
            store.append("open_question", p.open_question)

    # ---- Phase 7: coverage gate (100% of attributes have a record) ----
    if len(produced) != len(attr_obs):
        raise AssertionError("Coverage gate failed: not every attribute produced a record")

    # ---- Phase 8: review (pluggable; AutoApprove in dev) + memory write ----
    n_approved = n_unresolved = n_memory = 0
    for p in produced:
        ri = records.review_item(
            root, scope, artifact_version_ref=p.draft["record_id"],
            review_question=f"Approve business meaning for {p.draft['source_object_name']}."
                            f"{p.draft['source_attribute_name']}?")
        store.append("review_item", ri)

        if p.from_memory:
            store.append("source_dictionary_attribute", p.draft)  # already APPROVED via prior decision
            n_approved += 1
            n_memory += 1
            continue

        if not p.resolved:
            rd = records.review_decision(
                root, scope, review_item_ref=ri["record_id"], decision="DEFER",
                decision_maker="system", rationale="Deferred pending answer to the open question.")
            store.append("review_decision", rd)
            store.append("source_dictionary_attribute", p.draft)  # stays DRAFT/UNRESOLVED
            n_unresolved += 1
            continue

        outcome = review_policy.review(ri, p.draft)
        rd = records.review_decision(
            root, scope, review_item_ref=ri["record_id"], decision=outcome.decision,
            decision_maker=outcome.decision_maker, rationale=outcome.rationale,
            impact_scope=[p.draft["record_id"]])
        store.append("review_decision", rd)

        if outcome.decision == "APPROVE":
            approved = dict(p.draft)
            approved["lifecycle_state"] = "APPROVED"
            approved["review_decision_ref"] = rd["record_id"]
            approved["updated_at"] = C.now_iso()
            require_valid(root, C.C_DICT_ATTR, approved)
            store.append("source_dictionary_attribute", approved)
            memory.write_decision(p.subject_key, rd, payload=p.approved_values)  # the write-path
            n_approved += 1
        else:
            store.append("source_dictionary_attribute", p.draft)

    return RunResult(
        run_id=scope.run_id, context_snapshot_id=ctx.snapshot_id,
        n_attributes=len(produced), n_approved=n_approved,
        n_deferred_unresolved=n_unresolved, n_reused_from_memory=n_memory,
        open_questions=[p.open_question["question_text"] for p in produced if p.open_question],
        table_counts=store.counts())
