"""End-to-end test for the SDD slice against a REAL catalog + the memory loop."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from fixtures.build_source_db import build as build_source_db

from agentic_data_modeler.slice.llm import DeterministicStubLLM
from agentic_data_modeler.slice.memory import EpisodicMemory
from agentic_data_modeler.slice.orchestrator import run_sdd_agent
from agentic_data_modeler.slice.persistence import RecordStore
from agentic_data_modeler.slice.review import AutoApprovePolicy
from agentic_data_modeler.slice.source_binding import load_binding

TOTAL_ATTRIBUTES = 19   # pc_driver(6) + pc_policy(7) + pc_claim(6)
OPAQUE_COLUMNS = 1      # pc_policy.col_9


@pytest.fixture(scope="module")
def binding():
    build_source_db(ROOT / "tests/fixtures/proof_slice_source.duckdb")   # real catalog from SQL fixture
    return load_binding(ROOT)


def _run(binding, run_id, memory, tmp_path):
    inventory = binding.read_inventory()               # reads information_schema, no hardcoded schema
    store = RecordStore(tmp_path / f"store_{run_id}.json")
    result = run_sdd_agent(
        ROOT, binding.scope(run_id=run_id), inventory,
        memory=memory, store=store, review_policy=AutoApprovePolicy(), llm=DeterministicStubLLM(),
        pack_id=binding.pack_id, pack_version=binding.pack_version,
        geography=binding.geography, pack_domains=binding.pack_domains)
    return result, store


def test_reads_real_catalog_and_produces_reviewed_dictionary(binding, tmp_path):
    memory = EpisodicMemory(tmp_path / "mem.json")
    result, store = _run(binding, "RUN-1", memory, tmp_path)

    assert result.n_attributes == TOTAL_ATTRIBUTES
    assert result.n_deferred_unresolved == OPAQUE_COLUMNS       # opaque column never guessed
    assert result.n_approved == TOTAL_ATTRIBUTES - OPAQUE_COLUMNS
    assert result.context_snapshot_id                           # real snapshot, not None
    assert len(store.all("source_dictionary_attribute")) == TOTAL_ATTRIBUTES
    assert len(memory.all_decisions()) == TOTAL_ATTRIBUTES - OPAQUE_COLUMNS


def test_second_run_reuses_prior_decisions(binding, tmp_path):
    memory = EpisodicMemory(tmp_path / "mem.json")
    _run(binding, "RUN-1", memory, tmp_path)
    decisions_after_run1 = len(memory.all_decisions())

    result2, store2 = _run(binding, "RUN-2", memory, tmp_path)

    assert result2.n_reused_from_memory == TOTAL_ATTRIBUTES - OPAQUE_COLUMNS
    assert result2.n_deferred_unresolved == OPAQUE_COLUMNS      # opaque stays unresolved
    assert len(memory.all_decisions()) == decisions_after_run1  # idempotent: no re-litigation

    states = {d["business_name"]["evidence_state"]
              for d in store2.all("source_dictionary_attribute")}
    assert "DECIDED" in states                                  # reused from memory, not re-guessed
