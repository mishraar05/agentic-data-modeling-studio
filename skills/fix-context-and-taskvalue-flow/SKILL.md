---
name: fix-context-and-taskvalue-flow
description: >-
  Build spec for Genie Code to fix the two remaining run-blockers found by static
  screening: (1) assemble_context.py is a stub (builds a RuntimeRequest and stops) so no
  context_snapshot is written and the semantic phase has no input; (2) the task-value
  chain is broken — snapshot_source_metadata and assemble_context never emit the
  dbutils.jobs.taskValues the downstream tasks read, so profile/dictionary/relationships
  receive empty ids. Also decide the analyze_source_relationships stub. Use when the job
  reaches the context/semantic phase with empty snapshot/context ids. HARD RULE: reuse the
  existing builders (records.context_snapshot, slice.context), conform records to the DDL
  CHECK/NOT NULL, and never touch analyst/*, contracts, the loader, or metadata.
---

# Fix context assembly + task-value flow

## Status and authority

Version: `0.1.0-DRAFT` · Owner: solution/platform owner (`TBD`)
Static screening found two more blockers beyond imports and persistence. Fix them with
existing helpers — do NOT invent context logic or new record shapes.

### Verified findings
1. **`assemble_context.py` is a stub.** It builds `RuntimeRequest.from_parameters(...)`
   (ends ~line 81) and does nothing else: no `context_snapshot` record, no
   `context_snapshot_id`, no task values. The whole semantic phase
   (`analyze_source_dictionary`, `analyze_source_relationships`) depends on this.
2. **Broken task-value chain** — every `{{tasks.X.values.Y}}` in
   `resources/source_discovery.job.yml` requires task X to call
   `dbutils.jobs.taskValues.set(key="Y", ...)`. Missing:
   - `snapshot_source_metadata` must set `source_snapshot_id` — it currently sets nothing,
     but `profile_source` and `assemble_source_evidence` read
     `{{tasks.snapshot_source_metadata.values.source_snapshot_id}}`.
   - `assemble_context` must set `context_snapshot_id`, `source_snapshot_id`,
     `evidence_set_id` — `analyze_source_dictionary` and `analyze_source_relationships`
     read `{{tasks.assemble_context.values.*}}`.
   (`assemble_source_evidence` already sets `evidence_set_id`/`source_snapshot_id`, but the
   job reads those from `assemble_context`, so `assemble_context` must emit them.)
3. **`analyze_source_relationships.py` is also a stub** (ends ~line 93 on
   `RuntimeRequest.from_parameters`) — see §3 decision.

Prerequisite: apply `fix-notebook-imports` and `fix-control-table-persistence` first (this
skill assumes the control tables exist and the notebooks import cleanly).

---

## 0. PROTECTED — do not modify

- `src/agentic_data_modeler/analyst/**`, `contracts/**`, `generated/ddl/**`,
  `metadata/*.json`, `config/job_params.py`, the identity authorization check, and any
  passing test.
- Reuse existing record builders (`agentic_data_modeler.analyst.records` /
  `slice.records.context_snapshot`, `slice.context`); do NOT hand-write a `context_snapshot`
  shape or invent a fingerprint algorithm.

Golden rules: the **generated DDL is the source of truth** — every record must supply all
NOT NULL columns and every enum field must be within the DDL's `CHECK (... IN (...))`.
Never infer a schema; conform to `spark.table(target).schema` via the canonical
`_insert_records_idempotently` pattern.

---

## 1. Implement `assemble_context.py`

After the identity check, replace the dead-end (keep `RuntimeRequest` if used downstream):

- Resolve inputs for `RID = params["run_id"]` from the output schema
  (`params["output"]`): the committed `evidence_set` (its `record_id` → `evidence_set_ref`
  and `evidence_set_id`) and the `source_snapshot` (`record_id` → `source_snapshot_ref` /
  `source_snapshot_id`), both filtered by `solution_run_ref == RID`.
- Build the approved knowledge-pack slice and glossary the semantic phase uses — the same
  way `analyze_source_dictionary.py` does (`select_approved_pack`, `slice.context._load_glossary`),
  and reuse `slice.context.assemble_context(...)` / `records.context_snapshot(...)` to
  produce a contract-shaped `context_snapshot` record. Do not invent the fields.
- Write the `context_snapshot` record via the canonical `_insert_records_idempotently`
  (MERGE on `record_id`, verify count == 1) to
  `params["output"]["catalog"].params["output"]["schema"].context_snapshot`.
- `context_snapshot` NOT NULL columns to satisfy (per DDL): envelope
  (`record_id, schema_version, lob, domain, artifact_version, lifecycle_state, provenance,
  created_at, updated_at`) + `solution_run_ref, evidence_set_ref, snapshot_timestamp,
  knowledge_pack_id, knowledge_pack_version, selected_modules, context_effective_date,
  context_size_bytes, context_fingerprint, budget_compliance`. `lifecycle_state` must be
  `COMMITTED` (CHECK: COMMITTED/SUPERSEDED).
- Then set the task values (see §2).

## 2. Emit the task values (the invariant)

Enforce: **for every `{{tasks.<task>.values.<key>}}` in the job YAML, that task's notebook
must call `dbutils.jobs.taskValues.set(key="<key>", value=...)`.** Concretely add:

- In `snapshot_source_metadata.py`, after `snapshot_id` is computed:
  ```python
  dbutils.jobs.taskValues.set(key="source_snapshot_id", value=snapshot_id)
  ```
- In `assemble_context.py`, after writing the context_snapshot:
  ```python
  dbutils.jobs.taskValues.set(key="context_snapshot_id", value=context_snapshot_id)
  dbutils.jobs.taskValues.set(key="source_snapshot_id", value=source_snapshot_id)
  dbutils.jobs.taskValues.set(key="evidence_set_id", value=evidence_set_id)
  ```

Verify nothing else is missing: `grep -oE "tasks\.[a-z_]+\.values\.[a-z_]+" resources/source_discovery.job.yml | sort -u`
and confirm each has a matching `taskValues.set` in the producing notebook.

## 3. Decide `analyze_source_relationships.py` (stub) — STOP and ask

It currently builds a `RuntimeRequest` and stops, so no relationships are produced. Two
acceptable outcomes — **ask the owner which**, do not guess:
- **Wire the agent:** read `params["models"]`, run the relationship agent
  (`analyst.relationships` / `assemble_relationship_context`) with the mandatory independent
  critic (mirror the dictionary notebook), and write `source_dictionary_relationship` /
  `relationship_candidate` records via the canonical merge. `export_source_dictionary` then
  fills its Relationships sheet.
- **Defer cleanly:** leave relationships out for now, but the task must **succeed as a
  no-op** (no error, writes nothing) and `export_source_dictionary` must tolerate zero
  relationship rows (it already treats them as optional). Confirm export does not fail on an
  empty Relationships set.

Either way the run must complete; do not leave a task that errors.

## 4. Mandatory validations

- `python -m py_compile src/workflows/*.py`; `pytest -q` baseline unchanged.
- Every `{{tasks.X.values.Y}}` in the job has a matching `taskValues.set` in task X (the §2 grep).
- `assemble_context` writes exactly one `context_snapshot` row for RID (all NOT NULL present,
  `lifecycle_state='COMMITTED'`) and sets the three task values.
- After a run: `analyze_source_dictionary` receives non-empty `context_snapshot_id` /
  `source_snapshot_id`; the semantic phase runs; the job reaches `export_source_dictionary`.

## 5. Stop / escalation

- The relationships decision in §3 -> STOP, ask the owner.
- A `context_snapshot` NOT NULL column has no source from the evidence_set / pack -> STOP,
  ask (do not fabricate a value); an enum value outside the DDL CHECK -> fix to a valid value.
- Any fix would need to change `analyst/*`, a contract, or the DDL -> STOP.

## Acceptance

`assemble_context` writes a contract-shaped `context_snapshot` and emits
`context_snapshot_id`/`source_snapshot_id`/`evidence_set_id`; `snapshot_source_metadata`
emits `source_snapshot_id`; every job task-value reference has a producer; the relationships
stub is resolved per the owner; and the semantic phase runs end to end with non-empty ids.
