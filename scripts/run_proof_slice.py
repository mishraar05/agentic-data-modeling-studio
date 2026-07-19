"""Run the SDD proof slice end-to-end, twice, to show the memory loop.

    python scripts/run_proof_slice.py

Reads a REAL catalog (information_schema) for the tables bound in
config/proof_slice.yaml, analyzes them, and auto-approves. Run 2 shares the same
episodic memory and reuses run 1's decisions instead of re-asking.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from fixtures.build_source_db import build as build_source_db

from agentic_data_modeler.slice.llm import DeterministicStubLLM
from agentic_data_modeler.slice.memory import EpisodicMemory
from agentic_data_modeler.slice.orchestrator import run_sdd_agent
from agentic_data_modeler.slice.persistence import RecordStore
from agentic_data_modeler.slice.review import AutoApprovePolicy
from agentic_data_modeler.slice.source_binding import load_binding


def _print(label, result):
    print(f"\n=== {label} ({result.run_id}) ===")
    print(f"  attributes analyzed : {result.n_attributes}")
    print(f"  approved            : {result.n_approved}")
    print(f"  reused from memory  : {result.n_reused_from_memory}")
    print(f"  deferred/unresolved : {result.n_deferred_unresolved}")
    for q in result.open_questions:
        print(f"    open question -> {q}")
    print(f"  persisted tables    : {result.table_counts}")


def main() -> None:
    out = Path(os.environ.get("SLICE_OUT", Path(tempfile.gettempdir()) / "sdd_slice_runs"))
    out.mkdir(parents=True, exist_ok=True)

    binding = load_binding(ROOT)                       # source + scope from config (D23-01/02)
    build_source_db(ROOT / "tests/fixtures/proof_slice_source.duckdb")  # dev: (re)build the fixture catalog
    inventory = binding.read_inventory()               # real information_schema read
    print(f"source: {binding.schema} tables={binding.tables}  ({inventory.column_count} columns)")

    memory = EpisodicMemory(out / "episodic_memory.json")
    llm, policy = DeterministicStubLLM(), AutoApprovePolicy()
    print(f"review policy: {policy.name}")

    def run(run_id):
        return run_sdd_agent(
            ROOT, binding.scope(run_id=run_id), inventory,
            memory=memory, store=RecordStore(out / f"store_{run_id}.json"),
            review_policy=policy, llm=llm, pack_id=binding.pack_id,
            pack_version=binding.pack_version, geography=binding.geography,
            pack_domains=binding.pack_domains)

    _print("RUN 1 (fresh memory)", run("RUN-1"))
    r2 = run("RUN-2")
    _print("RUN 2 (same memory — should reuse decisions)", r2)

    print("\nMemory loop proven:" if r2.n_reused_from_memory > 0 else "\nNo reuse detected:",
          f"run 2 reused {r2.n_reused_from_memory} prior decisions instead of re-asking.")


if __name__ == "__main__":
    main()
