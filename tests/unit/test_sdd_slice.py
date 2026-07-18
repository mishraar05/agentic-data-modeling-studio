"""End-to-end test for the SDD slice, including the episodic memory loop."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agentic_data_modeler.slice.llm import DeterministicStubLLM
from agentic_data_modeler.slice.memory import EpisodicMemory
from agentic_data_modeler.slice.orchestrator import run_sdd_agent
from agentic_data_modeler.slice.persistence import RecordStore
from agentic_data_modeler.slice.records import Scope
from agentic_data_modeler.slice.review import AutoApprovePolicy
from agentic_data_modeler.slice.synthetic import personal_auto_inventory

TOTAL_ATTRIBUTES = 17   # policy(6) + claim(6) + driver(5)
OPAQUE_COLUMNS = 1      # claim.col7


def _run(tmp_path, run_id, memory):
    scope = Scope("ENG-T", "personal_auto", "personal_auto_policy_claims", "WP-T", run_id)
    store = RecordStore(tmp_path / f"store_{run_id}.json")
    result = run_sdd_agent(
        ROOT, scope, personal_auto_inventory(), memory=memory, store=store,
        review_policy=AutoApprovePolicy(), llm=DeterministicStubLLM())
    return result, store


def test_first_run_produces_valid_reviewed_dictionary(tmp_path):
    memory = EpisodicMemory(tmp_path / "mem.json")
    result, store = _run(tmp_path, "RUN-1", memory)

    assert result.n_attributes == TOTAL_ATTRIBUTES
    assert result.n_deferred_unresolved == OPAQUE_COLUMNS      # opaque column not guessed
    assert result.n_approved == TOTAL_ATTRIBUTES - OPAQUE_COLUMNS
    assert len(result.open_questions) == OPAQUE_COLUMNS
    assert result.context_snapshot_id                          # real snapshot, not None
    # coverage: every attribute yielded exactly one dictionary record
    assert len(store.all("source_dictionary_attribute")) == TOTAL_ATTRIBUTES
    assert len(memory.all_decisions()) == TOTAL_ATTRIBUTES - OPAQUE_COLUMNS


def test_second_run_reuses_prior_decisions(tmp_path):
    memory = EpisodicMemory(tmp_path / "mem.json")
    _run(tmp_path, "RUN-1", memory)
    decisions_after_run1 = len(memory.all_decisions())

    result2, store2 = _run(tmp_path, "RUN-2", memory)

    # the whole point: run 2 reuses run 1's decisions instead of re-asking
    assert result2.n_reused_from_memory == TOTAL_ATTRIBUTES - OPAQUE_COLUMNS
    # opaque column stays unresolved — memory never fabricates it
    assert result2.n_deferred_unresolved == OPAQUE_COLUMNS
    # idempotent: no new decisions written for already-decided subjects
    assert len(memory.all_decisions()) == decisions_after_run1

    # reused attributes carry DECIDED (from memory), not a fresh INFERRED guess
    states = {d["business_name"]["evidence_state"]
              for d in store2.all("source_dictionary_attribute")}
    assert "DECIDED" in states
