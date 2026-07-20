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

Version: `0.3.0-DRAFT` · Owner: solution/platform owner (`TBD`)

ALREADY APPLIED (verified in the pulled codebase — Phases 1–3 below are now a
**verification checklist**, not fresh build work): shared `run_id` on all tasks;
`/Workspace`-safe `REPO_ROOT`; dictionary notebook on `resolve_job_params` +
`params["models"]` with the mandatory-critic guard (§1a); `build_full_source_dictionary_workbook`
in the exporter; and the `analyze_source_dictionary`, `analyze_source_relationships`,
`export_source_dictionary` tasks wired into the job.

STILL REQUIRED before a clean run: **the control-table persistence fix** —
`skills/fix-control-table-persistence` (regenerate DDL, add the `create_control_tables`
bootstrap task, replace the inferred-schema write in `register_solution_run`). The job
cannot get past `snapshot_source_metadata` until that is done, so run it FIRST.

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

## 1. VERIFY the build (already applied by prior work — do not rebuild)

These were implemented and committed already. Confirm each; only touch a file if the
check fails, and then per the PROTECTED rules above.

- **Mandatory independent critic (§1a).** `analyze_source_dictionary.py` reads
  `producer_endpoint`/`critic_endpoint` from `params["models"]` and raises
  `"Independent critic is mandatory..."` when the critic is empty or equals the producer;
  `critic` is never `None`. Check: `grep -n "Independent critic is mandatory\|params\[.models.\]" src/workflows/analyze_source_dictionary.py`. Also preflight
  `metadata/sdd_param.json`: `models.critic_endpoint` present, non-placeholder, and a
  different family from the producer (configured: producer `databricks-meta-llama-3-3-70b-instruct`,
  critic `databricks-claude-opus-4-8`). If placeholder/equal → STOP, ask the owner.
- **Full semantic exporter.** `build_full_source_dictionary_workbook(...)` exists in
  `export/data_dictionary_excel.py` (structural `build_source_dictionary_workbook`
  untouched). Sheets: `Cover, Objects, Attributes, Dictionary, Code Values, Open Questions`
  (+`Relationships`). Check: `grep -n "def build_full_source_dictionary_workbook" ...`.
- **Pipeline wired.** `resources/source_discovery.job.yml` has `analyze_source_dictionary`
  (after `assemble_context`), `analyze_source_relationships`, and a final
  `export_source_dictionary` depending on both. Check: `grep -n "task_key:" resources/source_discovery.job.yml`.
- **Export notebook.** `src/workflows/export_source_dictionary.py` uses `resolve_job_params`,
  the identity check, the `/Workspace`-safe `REPO_ROOT`, reads this run's records, and calls
  `build_full_source_dictionary_workbook`.

If any check fails, build that one piece per the original spec (structural builder + its
test stay untouched; new tests for new code); otherwise proceed.

## 2. PREREQUISITE — control-table persistence must be fixed first

The job cannot pass `snapshot_source_metadata` until `skills/fix-control-table-persistence`
is applied: regenerate the control DDL, add the `create_control_tables` bootstrap task
(after `validate_scope`, before `register_solution_run`), and replace the inferred-schema
write in `register_solution_run` with a contract-shaped idempotent merge. Do that FIRST,
then run below. If `create_control_tables` is not yet in the job, STOP and apply that skill.

## 4. Run the job (deploy + execute)

1. `databricks bundle validate -t dev` — must pass.
2. `databricks bundle deploy -t dev`.
3. `databricks bundle run source_discovery -t dev` and wait.
4. No `dev` target/credentials -> STOP after step 1 and hand back; invent nothing.

All tasks must reach **Succeeded**, ending with `export_source_dictionary`.

## 5. Fix run-time failures — run/fix/re-run until the job finishes

This is an **outer loop**: keep triggering the job and fixing what fails until every
task reaches Succeeded (ending with `export_source_dictionary`), or a stop condition
below is hit. Do not stop at the first failure and hand back a half-run; do not proceed
to validation until the whole job is green.

```
OUTER LOOP (repeat until the whole job Succeeds or a STOP fires):
  run:  databricks bundle deploy -t dev  &&  databricks bundle run source_discovery -t dev ; wait
  if all tasks Succeeded -> exit loop, go to §6.
  else, for the first failed task:
     1. Read that task's driver log: the real exception + traceback.
     2. Localize the cause to ONE file (a workflow notebook, the new exporter, or the YAML).
     3. Classify:
          - config/wiring (missing task-value, wrong grouped key, path) -> fix that file
          - permission/identity (grant, principal, host)               -> report to owner, never bypass the check
          - contract/schema mismatch                                   -> STOP and ask (protected)
     4. Make the minimal fix for that cause only.
     5. pytest -q -> full baseline still green (no passing test regresses); else REVERT this fix.
     6. Commit "run-fix: <task> <cause>" (one commit per cause).
  -> loop back and re-run the job.
```

TERMINATION / anti-thrash guards (so it never loops forever):
- **No-progress guard:** if the *same task* fails with the *same error* after your fix,
  do not re-apply variations blindly — STOP and report that error with the log.
- **Attempt cap:** after 5 full run→fix cycles without reaching green, STOP and hand
  back a summary of what's still failing and why.
- **Regression guard:** a previously-passing task or a passing test breaks after a fix
  -> REVERT that fix, STOP, report.
- **Protected guard:** if the only way past a failure touches a PROTECTED item, a
  contract, or a guard -> STOP and ask.

Never advance by disabling a task, dropping a dependency, hardcoding a run_id/path/secret,
or try/excepting past an error. Progress must come from fixing the real cause.

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
