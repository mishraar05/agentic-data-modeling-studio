---
name: refactor-metadata-followup-fixes
description: >-
  Build spec for Genie Code to fix the defects found by post-refactor validation of
  the metadata job-parameter migration, running one fix at a time in a strict
  apply->verify loop and finishing by deploying and running the Databricks job.
  Fixes: (1) migrate analyze_source_dictionary onto resolve_job_params + metadata
  models, (2) restore a single shared run_id across all source_discovery tasks,
  (3) remove the hardcoded per-user REPO_ROOT, (4) rewrite three stale bundle tests,
  (5) delete leftover shims. Use after the metadata/common.json + sdd_param.json
  refactor is applied. HARD RULE: never modify agent reasoning (analyst/*), the
  config loader, contracts, the metadata JSON, passing tests, or any guardrail.
---

# Follow-up fixes: metadata refactor defects (guarded, looped, job-verified)

## Status and authority

Version: `0.2.0-DRAFT` · Owner: solution/platform owner (`TBD`)
Prerequisite: the metadata refactor (`metadata/common.json` + `metadata/sdd_param.json`,
`config/job_params.py`, notebooks on `resolve_job_params`) is already applied.
This spec fixes the defects a validation run found in that work. It is **mechanical
and surgical**: change only what each fix names, verify after every change, and stop
the moment something that was passing starts failing.

Baseline before you start (record it): `pytest` == **260 passed, 4 failed, 2 errors**.
The 2 errors are a sandbox-only DuckDB `.wal` limitation — they pass on Databricks /
a real filesystem. Your target end state: **only the 4 named failures move to green;
the 260 passing tests stay green; the 2 DuckDB errors are unchanged.** If any *other*
test count moves, you broke something — stop and revert.

---

## 0. PROTECTED — never modify (this is the hard guardrail)

This code was built and tested deliberately. Do **not** edit, refactor, "improve",
reformat, or delete anything below. If a fix seems to require touching one of these,
**STOP and ask the owner** — do not proceed.

- `src/agentic_data_modeler/analyst/**` — all agent reasoning (SA1/SA2/SA3, critic,
  gap checks, confidence, episodic, orchestrator, records, relationships).
- `src/agentic_data_modeler/config/job_params.py` — the loader. It is correct. Do not
  change its signature or merge logic.
- `metadata/common.json`, `metadata/sdd_param.json`, `metadata/README.md` — finalized
  content and names. Do not rename, reshape, or add keys (you may only *read* them).
- `contracts/**` and `generated/ddl/**` — no schema or DDL changes in this task.
- The identity authorization check in every workflow (`current_user ==
  execution_principal`, workspace-host match, `source_access_granted`) — keep exactly.
- The critic-independence guard (`producer_endpoint == critic_endpoint -> raise`) —
  keep; never weaken or remove.
- Any test that is **currently passing** (all 260). You may only edit the 3 named
  stale tests in Fix 4. **Never edit a passing test to make new code pass** — if a
  passing test fails after your change, the change is wrong, not the test.

Golden rule: **tests are the specification.** When code and a passing test disagree,
the code is wrong. Only the 3 tests explicitly named in Fix 4 encode the *old*
contract and may be rewritten.

---

## Execution protocol — one fix at a time, in a loop

Do NOT batch all fixes and run once at the end. For **each** fix (1 -> 5, in order):

1. Read the target file(s) fully before editing.
2. Make only the change the fix describes.
3. Run the loop below and do not advance until it is green:

```
LOOP per fix:
  run:  pytest -q
  check:
    - the fix's own "Prove it" grep/assert passes
    - failed-test count is <= previous step (never higher)
    - the 260 baseline tests are still passing
  if a previously-passing test now fails:
    -> REVERT this fix's edits, re-run pytest to confirm baseline restored, STOP, report.
  if green:
    -> git add -p && commit with message "fix(N): <summary>"
    -> proceed to next fix
```

Committing after each green fix is mandatory — it gives a clean revert point so one
bad fix can never lose the earlier good ones.

---

## Fix 1 (BLOCKER) — migrate `analyze_source_dictionary.py` onto metadata

Only file to touch: `src/workflows/analyze_source_dictionary.py`. It is the one
notebook still on the old parallel config path; make it match the others.

Remove: the `config_file` widget + reads, `config = JobConfig.from_file(...)` and the
`JobConfig` use, the hand-built `args = {...}` dict, and the
`sys.path.append("/Workspace/Users/cleancoding109@gmail.com")` block (Fix 3 covers the
path).

Replace with the shared pattern:
```python
from agentic_data_modeler.config.job_params import resolve_job_params
DYNAMIC = ("context_snapshot_id", "source_snapshot_id")
for w in ("run_id", *DYNAMIC):
    dbutils.widgets.text(w, "")
params = resolve_job_params(dbutils, REPO_ROOT, dynamic_keys=("run_id", *DYNAMIC))
```
Endpoints come from metadata, not `env-config.yml`:
```python
producer_endpoint = params["models"]["producer_endpoint"]
critic_endpoint   = params["models"]["critic_endpoint"]
if producer_endpoint == critic_endpoint:                       # PROTECTED guard — keep
    raise ValueError("Critic endpoint must differ from the producer endpoint (independence).")
producer = DatabricksFoundationModel(producer_endpoint)
critic   = DatabricksFoundationModel(critic_endpoint) if critic_endpoint else None
```
Repoint remaining `args[...]`/`config.*` reads to the grouped `params[...]` paths,
mirroring `snapshot_source_metadata.py`.

Prove it: `grep -n "JobConfig\|config_file\|env-config" src/workflows/analyze_source_dictionary.py`
empty; `grep -rn 'params\["models"\]' src/workflows` non-empty.

## Fix 2 (BUG) — one shared `run_id` across all source_discovery tasks

Only file: `resources/source_discovery.job.yml`. Set **every** task's `run_id` to the
identical value (records key on `params["run_id"]`, so a shared value is what ties one
run's records together — `{{job.run_id}}` already makes it unique per run):
```yaml
run_id: source_discovery_{{job.run_id}}
```
Apply the same rule to any other multi-task job that shares a solution run.

Prove it: `grep -n "run_id:" resources/source_discovery.job.yml` shows one identical
value on every line; `test_all_source_tasks_share_one_generated_run_identity` passes
**unchanged** (it is a PROTECTED passing/target test — fix the YAML, never the test).

## Fix 3 (BUG) — remove the hardcoded per-user `REPO_ROOT`

Files: all ten workflow notebooks under `src/workflows/`. Replace every
`REPO_ROOT = Path("/Workspace/Users/cleancoding109@gmail.com/agentic-data-modeling-studio")`
with a deploy-agnostic root and delete the matching
`sys.path.append("/Workspace/Users/cleancoding109@gmail.com")` (derive from
`REPO_ROOT / "src"`). Use one shared helper; the requirement is simply: **no literal
user path anywhere.** Suggested:
```python
import os
from pathlib import Path
REPO_ROOT = Path(
    os.environ.get("BUNDLE_ROOT")
    or dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        .notebookPath().get().rsplit("/src/", 1)[0]
)
```
Prove it: `grep -rn "cleancoding109@gmail.com" src` empty.

## Fix 4 (STALE TESTS) — rewrite only these three

File: `tests/unit/test_source_discovery_bundle.py`. These three encode the *old*
contract and are the ONLY tests you may edit:

- `test_source_discovery_is_run_rooted_and_parameterized` — assert `job.parameters`
  exposes only `work_package_id`; scope/source/model params are absent from YAML (they
  live in `metadata/`); no legacy id.
- `test_bundle_declares_run_context_and_agent_variables` — assert `databricks.yml`
  declares exactly `resource_prefix`, `work_package_id`, `production_root_path`.
- `test_relationship_agent_has_independent_producer_and_critic` — endpoints no longer
  come from `job.parameters`. **STOP AND ASK the owner:** the relationship notebook
  currently wires no producer/critic/independence at all. If relationships should run
  the agent, wire `params["models"]` + the independence guard (mirror Fix 1) and
  assert it; if it is intentionally WIP, `pytest.mark.skip(reason=...)`. Do NOT delete
  the independence assertion silently.

Do not touch `test_job_executes_complete_source_to_relationship_flow` or
`test_discovery_freezes_manifest_for_downstream_tasks` (passing).

## Fix 5 (CLEANUP) — delete leftover shims

- Delete `src/agentic_data_modeler/job_params.py` (deprecation shim) only after
  `grep -rn "agentic_data_modeler.job_params import\|from agentic_data_modeler import job_params" src tests`
  is empty.
- `find src -name '*.pyc' -path '*registration*' -delete` (source already gone).

---

## 6. RUN THE JOB — deploy and execute as final proof

Passing unit tests are necessary but not sufficient; the parameters only fully resolve
on Databricks. After all fixes are green locally:

1. `databricks bundle validate -t dev` — must pass.
2. `databricks bundle deploy -t dev`.
3. Run the job and wait for the result:
   `databricks bundle run source_discovery -t dev`
4. Inspect the run: every task **Succeeded**; confirm from the task logs / control
   tables that all tasks wrote records under the **same** `run_id`
   (`source_discovery_<job.run_id>`) — this is the live check for Fix 2.
5. If any task fails: read that task's driver log, map the error back to the specific
   fix, correct **only** that fix's file, re-run the local loop, then re-deploy and
   re-run. Repeat until the job succeeds end to end. **Do not** work around a failure
   by editing protected code, weakening a guard, or hardcoding a value.

If a `dev` target/workspace is not configured or credentials are unavailable, STOP
after step 1 and hand back to the owner with the validated bundle — do not invent
credentials or targets.

---

## Mandatory validations (all must pass)

- `pytest` — the 4 named failures now green; the 260 baseline tests still green; only
  the 2 sandbox DuckDB `.wal` errors remain (unchanged).
- `grep -rn "cleancoding109@gmail.com" src` → empty.
- `grep -n "JobConfig\|env-config" src/workflows/analyze_source_dictionary.py` → empty.
- `grep -n "run_id:" resources/source_discovery.job.yml` → one identical value per line.
- `grep -rn 'params\["models"\]' src/workflows` → non-empty.
- `databricks bundle validate -t dev` passes; `databricks bundle run source_discovery -t dev`
  finishes with all tasks Succeeded and one shared `run_id`.

## Stop / escalation (do not guess past these)

- Any change would touch a PROTECTED item (Section 0) -> STOP, ask.
- A previously-passing test fails after a fix -> REVERT that fix, STOP, report.
- The relationship-notebook decision in Fix 4 (WIP vs wire-the-agent) -> STOP, ask.
- No `dev` target/credentials for the job run -> STOP after `bundle validate`, hand back.
- `REPO_ROOT` cannot be derived without a user literal in this repo's setup -> surface
  it, do not reintroduce a hardcoded path.

## Acceptance

Only the 4 named defects fixed; every PROTECTED item untouched; each fix committed
separately; full suite green (bar the 2 sandbox DuckDB errors); `bundle validate`
green; and the `source_discovery` job runs end to end on `dev` with all tasks
succeeding under one shared `run_id`.
