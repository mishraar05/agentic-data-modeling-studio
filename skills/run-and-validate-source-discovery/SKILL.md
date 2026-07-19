---
name: run-and-validate-source-discovery
description: >-
  Build spec for Genie Code to make the source_discovery SDD pipeline run end to end
  and finish by producing the full semantic Source Data Dictionary as an Excel
  workbook. It wires the missing dictionary + export tasks, runs the Databricks job,
  fixes run-time failures surgically without breaking existing code, and validates
  every intermediate artifact and the final semantic Excel. Use when the user wants
  the SDD job to run end to end ending with Excel generation. HARD RULE: never modify
  agent reasoning (analyst/*), the config loader, contracts, metadata JSON, passing
  tests, or any guardrail; fix issues by cause, never by hardcoding or weakening a check.
---

# Run + validate: SDD end to end, ending with the semantic Excel

## Status and authority

Version: `0.2.0-DRAFT` · Owner: solution/platform owner (`TBD`)
Prerequisite: the metadata refactor and the follow-up fixes are applied and `pytest`
is green (bar the 2 sandbox-only DuckDB `.wal` errors). In particular Fix 1 of
`refactor-metadata-followup-fixes` (dictionary notebook on `resolve_job_params` +
`params["models"]`) must be done first, because this spec puts that notebook in the job.

Goal (owner-confirmed): the `source_discovery` job runs **end to end and ends by
writing the full semantic Source Data Dictionary as an .xlsx** — business names,
definitions, code-value meanings, confidence, and trust state, alongside the structural
columns.

Decisions locked by the owner:
1. Final Excel = **full semantic SDD** (not structural-only).
2. **Add** `analyze_source_dictionary` into the job.
3. Excel is produced by a **final job task**.
4. The **independent critic is mandatory** — the dictionary phase must run a real
   critic on a *different* model from the producer. A run with the critic missing or
   skipped is a FAILURE, not a pass (see §1a and the validations).

---

## 0. PROTECTED — never modify (hard guardrail)

Do not edit, refactor, reformat, or delete any of these to make a run pass. If a fix
seems to need one, **STOP and ask the owner.**

- `src/agentic_data_modeler/analyst/**` — all agent reasoning.
- `src/agentic_data_modeler/config/job_params.py` — the loader.
- `metadata/common.json`, `metadata/sdd_param.json`, `metadata/README.md` — read only.
- `contracts/**`, `generated/ddl/**` — no schema/DDL edits in this task.
- The identity authorization check and the critic-independence guard in the workflows.
- The existing `build_source_dictionary_workbook` (structural) and its test
  `tests/unit/test_data_dictionary_excel.py` — leave both intact (see Phase 1: add a
  NEW builder instead of changing the structural one).
- Any currently-passing test.

Golden rules: **tests are the specification** — never edit a passing test to make new
code pass. **Fix failures by their cause, never by hardcoding, swallowing an error,
weakening a guard, or loosening a contract.** Secrets stay in the runtime identity /
bundle, never in code or metadata.

What you MAY add/change in this task (new or export-surface code only): a new full-SDD
exporter function, a new export workflow notebook, new job tasks in
`resources/source_discovery.job.yml`, and NEW tests for the new code.

---

## 1a. Make the independent critic mandatory (fail closed)

The orchestrator (`analyst/*`, PROTECTED) already runs the critic when a critic model
is passed and folds critic agreement into confidence. The gap is only at the notebook
boundary: today `analyze_source_dictionary.py` does
`critic = DatabricksFoundationModel(critic_endpoint) if critic_endpoint else None`,
which **silently skips the critic** if the endpoint is blank. Close that:

- Preflight `metadata/sdd_param.json`: `models.critic_endpoint` must be present,
  non-empty, not a `REPLACE_*` placeholder, and **different** from
  `models.producer_endpoint`. If it is missing/placeholder, **STOP and ask the owner**
  for a real, distinct critic serving endpoint — do not run without it. The
  owner-configured pairing is producer `databricks-meta-llama-3-3-70b-instruct` and
  critic `databricks-claude-opus-4-8` (different families, both in-perimeter); confirm
  the critic is on a different model family from the producer, not just a different name.
- In the dictionary notebook (this edit is to a workflow notebook, allowed — not
  `analyst/*`), require the critic instead of defaulting to `None`:
  ```python
  critic_endpoint = params["models"]["critic_endpoint"]
  if not critic_endpoint or critic_endpoint == params["models"]["producer_endpoint"]:
      raise ValueError("Independent critic is mandatory: set a distinct models.critic_endpoint.")
  critic = DatabricksFoundationModel(critic_endpoint)   # never None in this pipeline
  ```
  Keep the existing independence guard (`producer == critic -> raise`). Do NOT change
  the orchestrator to force this — enforce it at the notebook, so `analyst/*` stays
  untouched and `critic_model` is simply never `None` here.

Prove it: the notebook has no `... if critic_endpoint else None` for the critic;
`grep` confirms it raises when the critic is absent or equal to the producer.

## 1. Build the semantic SDD exporter (additive — do not touch the structural one)

In `src/agentic_data_modeler/export/data_dictionary_excel.py`, add a NEW function
(keep `build_source_dictionary_workbook` unchanged so its test stays green):

```python
def build_full_source_dictionary_workbook(
    objects, attributes, dictionary_attributes, code_values,
    open_questions, relationships=None, *, meta, out_path,
) -> Path: ...
```
Sheets, in order:
- `Cover` — run id, catalog, schema, scope mode, snapshot ids, counts (objects,
  attributes, dictionary attributes, UNRESOLVED, privacy-flagged, code values).
- `Objects` — reuse the structural object rows.
- `Attributes` — reuse the structural attribute rows.
- `Dictionary` — one row per `source_dictionary_attribute`: Object, Attribute,
  Business Name, Business Definition, Name Trust (evidence_state), Definition Trust,
  Confidence, Evidence Count, Privacy, Lifecycle State, Review Decision.
- `Code Values` — one row per `source_dictionary_code_value`: Object, Attribute, Code,
  Meaning, Trust, Confidence.
- `Open Questions` — one row per `open_question`: Type, Object, Attribute, Question.
- `Relationships` (only if `relationships` provided) — From, To, Type, Trust, Confidence.

Deterministic and LLM-free: it only renders records already produced by the agents.
Add a NEW test `tests/unit/test_full_dictionary_excel.py` asserting: sheet names in the
order above; Dictionary row count == number of dictionary_attributes; Code Values count
== code_value records; UNRESOLVED attributes show no invented value; no fabricated
evidence ids leak into any cell.

## 2. Wire the pipeline (job YAML)

In `resources/source_discovery.job.yml`, using the shared-run-id rule
(`run_id: source_discovery_{{job.run_id}}` on every task):

- Add task `analyze_source_dictionary` -> `depends_on: assemble_context`, passing the
  dynamic task-values it needs (`context_snapshot_id`, `source_snapshot_id`), reusing
  the notebook already migrated in Fix 1.
- Keep `analyze_source_relationships` (depends on `assemble_context`) — runs alongside.
- Add a final task `export_source_dictionary` ->
  `depends_on: [analyze_source_dictionary, analyze_source_relationships]`, pointing at a
  new notebook `src/workflows/export_source_dictionary.py`.

## 3. Build the export notebook

`src/workflows/export_source_dictionary.py` — mirror the other workflows exactly:
`resolve_job_params(...)`, the identity authorization check, `REPO_ROOT` derived (no
user literal). Then, for `RID = params["run_id"]`, read from the output catalog/schema:
`source_object_observation`, `source_attribute_observation`, `source_dictionary_object`,
`source_dictionary_attribute`, `source_dictionary_code_value`, `open_question`, and
(optional) `source_dictionary_relationship` — all filtered to RID. Call
`build_full_source_dictionary_workbook(...)` and write the `.xlsx` to a stable path
(a UC Volume under the output catalog, or the bundle workspace files path). Print/emit
the written path as a task value.

Do not embed business logic here — it only reads records and renders. No new
approvals, no re-derivation of meaning.

## 4. Run the job (deploy + execute)

1. `databricks bundle validate -t dev` — must pass.
2. `databricks bundle deploy -t dev`.
3. `databricks bundle run source_discovery -t dev` and wait.
4. No `dev` target/credentials -> STOP after step 1 and hand back; invent nothing.

All tasks must reach **Succeeded**, ending with `export_source_dictionary`.

## 5. Fix run-time failures — surgical loop

For each failed task:
```
LOOP:
  1. Read that task's driver log: the real exception + traceback.
  2. Localize the cause to ONE file (a workflow notebook, the new exporter, or the YAML).
  3. Classify:
       - config/wiring (missing task-value, wrong grouped key, path) -> fix that file
       - permission/identity (grant, principal, host)               -> report to owner, never bypass the check
       - contract/schema mismatch                                   -> STOP and ask (protected)
  4. Minimal fix for that cause only.
  5. `pytest -q` -> full baseline still green (no passing test regresses).
  6. Redeploy + re-run.
  7. New task fails -> repeat. A previously-passing task fails -> REVERT, STOP, report.
  8. Green -> commit "run-fix: <task> <cause>" (one commit per cause).
```
Never advance by disabling a task, dropping a dependency, hardcoding a run_id/path,
or try/excepting past an error. If the only way through touches a PROTECTED item, STOP.

Do not validate until the whole job (including export) succeeds.

## 6. Validate intermediate results (for THIS run)

`RID = source_discovery_<job.run_id>`. Output catalog/schema come from
`metadata/common.json` (`output.catalog`/`output.schema`). Confirm records exist for RID
and are consistent:

| Task | Table(s) | Assertions |
|---|---|---|
| register_solution_run | `solution_run` | 1 row for RID; lob/domain/catalog/schema match `common.json` |
| snapshot_source_metadata | `source_snapshot`, `source_object_observation`, `source_attribute_observation` | 1 snapshot; ≥1 object; ≥1 attribute; counts match in-scope tables; dense ordinals |
| profile_source | `profile_snapshot`, `profile_evidence`, `evidence_item` | 1 profile snapshot referencing the source snapshot; refs resolve |
| assemble_source_evidence | `evidence_set`, `evidence_item` | 1 evidence_set; item count matches rows; refs resolve |
| assemble_context | `context_snapshot` | 1 snapshot referencing the evidence_set |
| analyze_source_dictionary | `source_dictionary_object/attribute/code_value`, `validation_finding`, `open_question`, `review_item` | **100% coverage** (one dictionary_attribute per attribute observation); INFERRED values carry ≥1 real evidence_ref; no fabricated ids; UNRESOLVED -> open_question; nothing auto-APPROVED; privacy-flagged routed to a steward; **the independent critic actually executed** (see cross-cutting) |
| analyze_source_relationships | `source_dictionary_relationship`/`relationship_candidate` | candidates reference in-scope objects only; DRAFT/contract-gated |

Cross-cutting: **single run identity** (all rows under one RID — live proof of the
run_id fix); referential integrity (every ref resolves); records validate against their
`contracts/*.schema.json` (reuse the existing validator; do not alter contracts); trust
states within OBSERVED/INFERRED/DECIDED/UNRESOLVED.

**Independent critic ran (mandatory).** Prove the critic executed on a different model,
not merely that an endpoint was configured: the dictionary attributes carry a
critic-agreement signal in their confidence (the orchestrator writes it via
`apply_critic_agreement`), and/or the run summary/metric records a non-null
`critic_findings` count. Confirm the critic model != producer model. If there is no
evidence the critic ran, treat the run as FAILED and report it — do not accept a
gap-checks-only run as a pass.

## 7. Validate the final semantic Excel

- The `.xlsx` exists at the export path for RID and opens.
- Sheets: `Cover, Objects, Attributes, Dictionary, Code Values, Open Questions`
  (+`Relationships` if any).
- `Dictionary` rows == `source_dictionary_attribute` count for RID == attribute
  observation count (100% coverage carried through to the workbook).
- `Code Values` rows == `source_dictionary_code_value` count for RID.
- Every INFERRED business name/definition cell has a non-empty value and a trust state;
  every UNRESOLVED one is blank with a matching Open Questions row.
- No fabricated evidence id or invented value appears anywhere in the workbook.
- Cover counts match §6.

## 8. Validation report

Write a short report (outputs/workspace): per-task table + row counts, cross-cutting
results, the Excel checks, RID, the export path, and the job run URL. Present it. Do not
claim success unless every §6 and §7 check passed.

## Mandatory validations (all must pass)

- `pytest` baseline green + the new exporter test green; no passing test regressed.
- Job runs end to end on `dev`; all tasks Succeeded, ending with `export_source_dictionary`.
- Every §6 table has rows under one shared RID; 100% dictionary coverage; nothing
  auto-approved; privacy routed; contracts validate.
- The **independent critic ran** on a distinct model (proven per §6 cross-cutting), and
  `models.critic_endpoint` was a real, non-placeholder endpoint != producer.
- The semantic `.xlsx` has the expected sheets, coverage carried through, no fabricated
  content, cover counts matching.
- No PROTECTED item modified; no hardcoded run_id/path/secret; structural builder + its
  test untouched.

## Stop / escalation

- No `dev` target/credentials -> STOP after `bundle validate`.
- `models.critic_endpoint` missing, placeholder, or == producer -> STOP and ask the
  owner for a real, distinct critic endpoint; never run the dictionary phase without it.
- A failure whose only fix touches a PROTECTED item, a contract, or a guard -> STOP, ask.
- Permission/identity failure -> report the needed grant; never bypass the identity or
  independence check.
- A previously-passing task/test regresses after an edit -> REVERT, STOP, report.
- Any §6/§7 check fails after a successful run -> report as a defect; never massage data
  or edit a contract to make it pass.

## Acceptance

The `source_discovery` job runs end to end under one shared run id and ends by writing
the full **semantic** SDD Excel; every intermediate artifact is present, contract-valid,
referentially sound, and 100%-covered with no auto-approval or privacy leakage; the
workbook faithfully reflects those records; a validation report is delivered; and no
protected code, test, contract, or guardrail was touched.
