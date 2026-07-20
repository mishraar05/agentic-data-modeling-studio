---
name: fix-control-table-persistence
description: >-
  Build spec for Genie Code to fix the source_discovery persistence failures the right
  way: (1) regenerate the control DDL from the current contracts, (2) add a control-table
  bootstrap that applies that DDL to the configured output schema, (3) complete
  register_solution_run so it writes a contract-shaped solution_run record via the
  canonical idempotent-merge pattern, and (4) undo the ad-hoc writes to the wrong catalog
  with inferred schemas. Use when tasks fail with "Expected one registered solution run;
  found 0", schema cast errors (STRING/ARRAY/STRUCT), or missing control tables. HARD
  RULE: the generated DDL is the ONLY source of truth for table schema — never infer or
  hand-write a schema, never write outside the configured output catalog/schema, never
  DROP a table without owner approval, never touch analyst/* or contracts logic.
---

# Fix control-table persistence (solution_run + bootstrap)

## Status and authority

Version: `0.1.0-DRAFT` · Owner: solution/platform owner (`TBD`)
This fixes a real, verified failure chain — not a guess. Follow the diagnosis; do not
re-diagnose by trial-and-error against the live workspace.

### Verified root causes (current committed state — do not re-litigate)
1. **No bootstrap.** `src/schema_builder/` generates `generated/ddl/control/*.sql`, but
   nothing applies it. Writers use `spark.table(target).schema`, which requires the table
   to already exist. On a fresh catalog the first write (solution_run) has no table.
   There is no `create_control_tables` notebook and no create task in the job.
2. **`register_solution_run.py` now writes, but wrongly.** After
   `RuntimeRequest.from_parameters(...)` a committed block (`# §6: Persist solution run`,
   ~lines 83–108) writes only **8 columns** via `spark.createDataFrame([dict])` +
   `df.write.mode("append").option("mergeSchema","true").saveAsTable(...)` — an INFERRED,
   PARTIAL schema. It targets the correct location (`params["output"]` →
   `insurance_source_discovery.control.solution_run`) but omits every other NOT NULL column
   (schema_version, provenance, workflow_state, source_tables, timestamps, status, …) and
   lets Spark create/mangle the table. This must be REPLACED (§3).
3. **Earlier `main.modeler` / inferred-schema experiments were reverted** — no
   `main.modeler` remains in `src`. But the committed write in #2 is the same
   inferred-schema anti-pattern that caused the STRING→ARRAY→STRUCT cast churn.
4. **Stale DDL** — `solution_run.sql` is still generated from contract `v0.2.0` and still
   has `authorization_ref NOT NULL` (a registration remnant); regenerate from current contracts.

### The canonical pattern already exists — copy it
`snapshot_source_metadata.py :: _insert_records_idempotently(table, records)`:
resolves `{output_catalog}.{output_schema}.<table>`, reads `spark.table(target).schema`
(table pre-created by DDL), `createDataFrame(records, schema=target_schema)`, `MERGE ...
ON record_id WHEN NOT MATCHED THEN INSERT *`, then verifies the persisted count. Reuse
this exact shape for `solution_run`.

---

## 0. PROTECTED / non-negotiable rules

- The **generated DDL is the ONLY source of truth** for any table's schema. Never infer a
  schema from Python objects, never hand-write `CREATE TABLE`, never invent or drop columns.
- Write **only** to `params["output"]["catalog"]` / `params["output"]["schema"]`
  (`insurance_source_discovery.control`). Never `main.modeler` or any other location.
- Never `DROP TABLE` without explicit owner approval (see §4). Control tables may hold
  prior run rows.
- Do not touch `analyst/**`, the contract *logic*, `config/job_params.py`, `metadata/*.json`,
  or the identity authorization check. (Regenerating DDL from contracts in §1 is allowed;
  editing contract *content* is not, except the §1 reconciliation the owner approves.)
- `src/schema_builder/**` and `generated/ddl/**` are generator + generated output — run the
  generator; do not hand-edit generated SQL.

---

## 1. Regenerate the control DDL from current contracts

Run the existing generator (`src/schema_builder/contract_to_ddl.py` /
`ddl_generator.py`) to regenerate `generated/ddl/control/*.sql` from the current
`contracts/*.schema.json`. Then reconcile the `solution_run` remnant:
- If the current `solution_run` contract no longer has `authorization_ref` (registration
  was removed), the regenerated DDL must drop it too. Good.
- If the contract still requires `authorization_ref`/other registration fields, **STOP and
  ask the owner** whether to remove them from the contract (registration was supposed to be
  gone) — do not invent a value to satisfy a column that should not exist.
Commit the regenerated SQL. Do not hand-edit it.

## 2. Add a control-table bootstrap (the missing structural piece)

Create `src/workflows/create_control_tables.py` — same header as other notebooks
(`resolve_job_params`, `/Workspace`-safe `REPO_ROOT`, identity check). It must:
- Read the regenerated `generated/ddl/control/*.sql` from `REPO_ROOT`.
- Execute each statement with `spark.sql(...)`; the DDL already uses
  `CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.<t>` and `ALTER TABLE ...
  ADD CONSTRAINT` — idempotent by design. Guard the ALTERs so re-runs don't fail on
  already-existing constraints (catch/ignore "already exists").
- Target catalog/schema come from `params["output"]` — assert they equal what the DDL was
  generated for; if they differ, STOP (do not create tables in an unexpected location).

Wire it into `resources/source_discovery.job.yml` as a task **after `validate_scope`,
before `register_solution_run`** (e.g. `create_control_tables` depends_on `validate_scope`;
`register_solution_run` depends_on `create_control_tables`). Shared `run_id` rule applies.

## 3. Replace the write in `register_solution_run.py` — do it correctly

**Delete the committed `# §6: Persist solution run` block (~lines 83–108: the
`_qualified` helper's ad-hoc use, the 8-column `solution_run_data` dict, the
`spark.createDataFrame([...])` and `df.write...saveAsTable(...)`).** In its place, build ONE
`solution_run` record dict whose keys/types match the **regenerated** `solution_run` DDL,
and persist it with a local copy of the canonical `_insert_records_idempotently` pattern
from `snapshot_source_metadata.py` (target `solution_run`, MERGE on `record_id`, verify
count == 1). Do NOT infer schema and do NOT use `saveAsTable`/`mergeSchema`; the table is
pre-created by §2 and you conform to `spark.table(target).schema`. Field mapping (reconcile
against the regenerated schema — if a NOT NULL column has no mapping here, STOP and ask
rather than inventing):

- `record_id` = `params["run_id"]`
- `schema_version` = the `solution_run` contract's version (read it; do not hardcode a guess)
- `lob`/`domain` = `params["scope"]`
- `artifact_version` = the constant this repo already uses for run-rooted records
- `lifecycle_state` = `"ACTIVE"` (valid per the CHECK: ACTIVE/CLOSED/REJECTED/SUPERSEDED)
- `provenance` = struct `{run_id, context_snapshot_id:None, source_snapshot_id:None, profile_snapshot_id:None, model_version:None, prompt_version:None, skill_version:None, tool_version:None}`
- `created_at`/`updated_at`/`start_timestamp`/`end_timestamp` = `now` (tz-naive, as snapshot does)
- `workflow_state` = `"VALIDATED"` (first valid state per the CHECK)
- `source_catalog`/`source_schema` = `params["source"]`
- `source_tables` = `json.loads(params.get("source_tables") or "[]")` — a real **list** (ARRAY<STRING>), NOT a JSON string (this is the STRING→ARRAY cast error's cause)
- `source_product`/`source_module`/`source_version` = `params["source"]` (nullable)
- `knowledge_pack_id`/`knowledge_pack_version` = `params["knowledge_pack"]` (nullable)
- `output_catalog`/`output_schema` = `params["output"]`
- `source_access_granted` = `params["identity"]["source_access_granted"].lower() == "true"` (BOOLEAN)
- `profiling_policy` = `params["profiling"]["policy_id"]`
- `run_type` = `"SOURCE_DISCOVERY"`; `status` = `"RUNNING"`
- `error_message` = None; `cost_usd` = None

Keep the identity check above unchanged. Remove any earlier ad-hoc write to `main.modeler`
or inferred-schema code.

## 4. Recreate any mis-shaped table left by the inferred write (owner-gated)

- The only write to `solution_run` must be §3's contract-shaped merge. Confirm no other
  writer remains: `grep -rn "saveAsTable\|mergeSchema\|main.modeler" src/workflows` should
  show nothing in `register_solution_run.py`.
- The committed inferred-schema write in root-cause #2 may already have created
  `insurance_source_discovery.control.solution_run` (and possibly other control tables) with
  a wrong 8-column schema on the workspace. Any such mis-shaped table must be recreated from
  the regenerated DDL. Recreating requires a DROP — **do not DROP autonomously.** Present the
  owner the exact table(s) and the `DROP TABLE ...;` + bootstrap re-create plan, and proceed
  only on approval. These tables hold only failed-run rows, but the DROP stays owner-gated.

## 5. Validate (local + live)

- Local: `pytest -q` baseline still green. If a bundle/DDL test exists, it passes.
- `databricks bundle validate -t dev` passes; `create_control_tables` runs before `register_solution_run`.
- After a run: `insurance_source_discovery.control.solution_run` exists with the DDL schema
  (not inferred); exactly **one** row for `RID = source_discovery_<job.run_id>`;
  `source_tables` is an ARRAY; `snapshot_source_metadata` passes ("found 1"); the pipeline
  proceeds past snapshot.
- `grep -rn "main.modeler" src` returns nothing.

## 6. Stop / escalation

- The regenerated DDL still requires a registration field (`authorization_ref`) -> STOP, ask.
- A NOT NULL column in §3 has no clean mapping -> STOP, ask (never invent to satisfy NOT NULL).
- Recreating a mis-shaped table needs a DROP -> STOP, get owner approval first.
- `params["output"]` differs from the DDL's target catalog/schema -> STOP (wrong location).
- Any fix would require inferring/hand-writing a schema or writing outside the configured
  output -> STOP; that violates the source-of-truth rule.

## Acceptance

Control DDL regenerated from contracts; a bootstrap task creates the control tables in
`insurance_source_discovery.control` before any write; `register_solution_run` persists
exactly one contract-shaped `solution_run` record via idempotent MERGE (correct location,
DDL schema, `source_tables` as ARRAY); no `main.modeler` or inferred-schema writes remain;
and the job proceeds past `snapshot_source_metadata` end to end.
