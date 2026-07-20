---
name: refactor-metadata-followup-fixes
description: >-
  Verification checklist for the metadata-refactor follow-up fixes. As of the latest
  pulled codebase these fixes are ALL APPLIED — this file now only verifies them and
  points to the two skills that still have outstanding work (control-table persistence
  and DuckDB removal). Use to confirm the follow-up fixes are in place before running
  the job. Do not re-apply; do not touch analyst/*, the loader, contracts, or passing tests.
---

# Follow-up fixes — APPLIED (verification only)

## Status

Version: `0.3.0` · Status: **all five fixes verified applied in the pulled codebase.**
This skill no longer changes code. Run the checks below; if one fails, re-apply only
that item per the notes. The two items that were NOT part of these fixes and remain
outstanding are called out at the end.

## Verify (each must hold)

1. **Dictionary notebook migrated (was Fix 1).** `src/workflows/analyze_source_dictionary.py`
   imports `resolve_job_params`, reads `params["models"]`, and enforces the mandatory
   independent critic. Check: `grep -n "resolve_job_params\|params\[.models.\]\|Independent critic is mandatory" src/workflows/analyze_source_dictionary.py` (non-empty); and
   `grep -n "JobConfig\|env-config" src/workflows/analyze_source_dictionary.py` (empty).
2. **Shared run_id (was Fix 2).** Every task in `resources/source_discovery.job.yml` uses
   `run_id: source_discovery_{{job.run_id}}`. Check: `grep -n "run_id:" resources/source_discovery.job.yml` — one identical value on every line.
3. **`/Workspace`-safe REPO_ROOT (was Fix 3).** All workflow notebooks derive `REPO_ROOT`
   with a `/Workspace` prefix; no literal user path. Check: `grep -rn "cleancoding109@gmail.com" src` (empty) and `grep -rln "startswith(\"/Workspace/\")" src/workflows` (all notebooks).
4. **Stale bundle tests rewritten (was Fix 4).** `tests/unit/test_source_discovery_bundle.py`
   asserts the new metadata contract (e.g. `params["models"]["producer_endpoint"]` in the
   notebook, independence guard), not the old `job.parameters`/`databricks.yml` variables.
5. **Shim deleted (was Fix 5).** `src/agentic_data_modeler/job_params.py` no longer exists;
   all imports use `config.job_params`.

If all five hold: this skill is complete — do nothing further here.

## Still outstanding (NOT covered by this skill)

- **Control-table persistence** → `skills/fix-control-table-persistence`. The DDL is still
  stale (`solution_run.sql` v0.2.0 with `authorization_ref`), there is no
  `create_control_tables` bootstrap, and `register_solution_run` still writes an inferred,
  partial (8-column) schema. This blocks the job at `snapshot_source_metadata`. Do this next.
- **DuckDB removal** → `skills/remove-duckdb`. DuckDB is still present in `evidence/sql_catalog.py`,
  `slice/source_binding.py`, `config/proof_slice.yaml`, `pyproject.toml`, etc.
- The relationship notebook's producer/critic/independence wiring (the Fix 4 stop-and-ask)
  — confirm with the owner whether relationships runs the agent or stays WIP.
