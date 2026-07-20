---
name: remove-duckdb
description: >-
  Build spec for Genie Code to remove DuckDB and the offline proof-slice test harness
  it powers from the repository, without breaking the canonical agent code or the
  Databricks workflows. Deletes the DuckDB CatalogReader, the slice source-binding and
  legacy run_sdd_agent harness, the proof-slice fixtures/config/script and its test, and
  the dev dependency. Use when removing DuckDB. HARD RULE: never touch agent reasoning
  (analyst/*), the shared slice.records/common/contracts/context modules, evidence
  metadata, contracts, metadata JSON, or any still-passing non-slice test.
---

# Remove DuckDB + the offline proof-slice harness

## Status and authority

Version: `0.1.0-DRAFT` · Owner: solution/platform owner (`TBD`)
Owner decision: remove DuckDB everywhere and **delete** the offline proof-slice harness
it powers (the SDD is validated on Databricks now). Surgical and dependency-aware:
delete only DuckDB-coupled files and their exclusive dependents; leave everything the
canonical agent and workflows import.

Why this is safe (verified dependency map):
- `analyst/*` and `src/workflows/*` import only `slice.records`, `slice.common`,
  `slice.contracts`, `slice.context` — **these stay**.
- `evidence.sql_catalog` (the DuckDB reader + `CatalogReader` protocol) is imported
  **only** by `slice.source_binding`; `evidence/__init__` does not export it.
- `slice.source_binding` and `slice.orchestrator` (`run_sdd_agent`) are imported **only**
  by `tests/unit/test_sdd_slice.py` and `scripts/run_proof_slice.py`.
- The real Databricks path builds `MetadataInventory.from_iterables(...)` from Spark
  (`evidence.metadata`), not from DuckDB — so nothing production depends on DuckDB.

---

## 0. PROTECTED — never modify or delete

- `src/agentic_data_modeler/analyst/**` — agent reasoning.
- `src/agentic_data_modeler/slice/records.py`, `slice/common.py`, `slice/contracts.py`,
  `slice/context.py` — imported by `analyst/*` and the real workflows. **Keep.**
- `src/agentic_data_modeler/evidence/metadata.py`, `evidence/assembly.py`,
  `evidence/profiling.py`, `evidence/__init__.py` — the real inventory path. **Keep.**
- `src/workflows/**`, `contracts/**`, `generated/ddl/**`, `metadata/*.json`,
  `config/job_params.py`.
- Any currently-passing test **except** `tests/unit/test_sdd_slice.py` (which is deleted
  because its harness is being removed). Never edit another passing test to compensate.

Golden rule: if removing a DuckDB reference would force a change to any PROTECTED file,
**STOP and ask** — that means the dependency map is different than expected.

---

## 1. DELETE these files (DuckDB + exclusive dependents)

- `src/agentic_data_modeler/evidence/sql_catalog.py`  (DuckDBCatalogReader + CatalogReader protocol)
- `src/agentic_data_modeler/slice/source_binding.py`  (binds proof_slice.yaml to the DuckDB reader)
- `src/agentic_data_modeler/slice/orchestrator.py`     (legacy `run_sdd_agent` harness)
- `src/agentic_data_modeler/slice/synthetic.py`        (removed-stub; only a DuckDB docstring reference)
- `scripts/run_proof_slice.py`
- `tests/unit/test_sdd_slice.py`
- `tests/fixtures/build_source_db.py`
- `tests/fixtures/proof_slice_source.duckdb`
- `tests/fixtures/proof_slice_source.sql`
- `config/proof_slice.yaml`

## 2. CONDITIONAL DELETE — the orphaned legacy slice modules

`slice/llm.py` (`DeterministicStubLLM`), `slice/memory.py` (`EpisodicMemory`),
`slice/persistence.py` (`RecordStore`), `slice/review.py` (`AutoApprovePolicy`) were
imported **only** by the harness deleted in §1. For each, first confirm no remaining
importer:
```
grep -rn "slice.llm\|slice.memory\|slice.persistence\|slice.review\|DeterministicStubLLM\|AutoApprovePolicy\|RecordStore" src tests scripts
```
Delete a module only if grep shows nothing (outside its own file). If any is still
imported (e.g. by `analyst/*` or another test), **keep it and report** — do not force it.

## 3. EDIT these files (remove DuckDB bits, keep the file)

- `pyproject.toml` — remove the `"duckdb>=1,<2",` line from the `[project.optional-dependencies] dev` list. Leave the rest untouched.
- `src/agentic_data_modeler/slice/__init__.py` — its `__all__ = ["orchestrator"]` names a
  now-deleted module; set `__all__ = []` and update the docstring to drop the
  `config/proof_slice.yaml` / DeterministicStub / AutoApprove description (the slice is no
  longer a runnable dev harness; it now only provides shared record/contract/context helpers).

## 4. Mandatory validations (all must pass)

- `grep -rin "duckdb" src tests config scripts pyproject.toml` returns nothing (ignore `__pycache__`/`.egg-info`).
- No dangling imports: `python -c "import agentic_data_modeler.slice, agentic_data_modeler.evidence"` succeeds.
- `pytest -q` — the 2 DuckDB `.wal` collection errors are **gone** (that test module was
  removed); the previously-passing suite is otherwise unchanged (no NEW failures, no lost
  passing tests beyond the intentionally-removed `test_sdd_slice`). Expected: same passing
  count, `0 errors`.
- `git status` shows only the intended deletions/edits.

## 5. Stop / escalation

- Any deletion would break a PROTECTED import (esp. `slice.records/common/contracts/context`,
  `evidence.metadata`) -> STOP; the dependency map differs, ask the owner.
- A §2 module still has an importer -> keep it, report it; do not delete.
- A non-slice test fails after removal -> REVERT, STOP, report (something depended on a
  removed module that the map missed).

## 6. Note for the sibling skills

Removing `test_sdd_slice.py` deletes the 2 sandbox-only DuckDB `.wal` errors referenced as
"baseline" in `refactor-metadata-followup-fixes` and `run-and-validate-source-discovery`.
After this runs, the baseline is simply "N passed, 0 errors" — those two skills' mentions
of "2 DuckDB errors (ignore)" no longer apply and should be read as "0 errors."

## Acceptance

DuckDB and the offline proof-slice harness are gone; the canonical agent, the shared
slice helpers, the evidence-metadata path, and the Databricks workflows are untouched and
importable; no DuckDB reference remains anywhere; and the test suite is green with zero
collection errors.
