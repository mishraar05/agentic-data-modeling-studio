---
name: refactor-job-parameters-metadata
description: >-
  Build spec for Genie Code to (1) move all Databricks job parameters into grouped
  JSON under metadata/ (common.json defaults + sdd_param.json overrides) read by a
  config-subpackage loader, (2) refactor every job + notebook to pass only dynamic
  task-values, (3) remove the `registration` authorization concept end-to-end, and
  (4) refactor the contract JSON + regenerate DDL accordingly. Use when refactoring
  job parameter management or removing registration. Do NOT change agent reasoning
  (analyst/*), contracts unrelated to registration, or business logic.
---

# Refactor: metadata-driven job parameters + remove registration

## Status and authority

Version: `0.2.0-DRAFT` · Owner: solution/platform owner (`TBD`)
Authority order: Requirements Charter → approved contracts → Agent Solution
Architecture + ADRs → this spec. Stop on conflict. This is a mechanical refactor:
**no change to agent reasoning (`analyst/*`), business logic, or contracts unrelated
to registration.**

Finalized by owner decisions: **grouped JSON**, files named **`common.json`**
(shared defaults) + **`sdd_param.json`** (overrides), **single environment**
(no dev/prod switch), dynamic values **excluded** from the JSON, loader in a
**config subpackage**, **registration removed**.

## Goal

1. All Databricks job parameters live in `metadata/common.json` + `metadata/sdd_param.json` (grouped, non-secret).
2. Each task passes only its dynamic task-values; a loader merges the two JSON files.
3. The `registration` authorization concept is removed everywhere.
4. Contract JSON + generated DDL refactored to drop registration-derived fields; DDL regenerated.
5. All existing unit tests pass; `databricks bundle validate` passes.

## 1. Metadata files (create)

Grouped, static + overrides only. **No** `run_id`, `work_package_id`,
`source_tables`, `source_snapshot_id`, `context_snapshot_id` (dynamic — passed as
task values). **No** secrets. **No** `registration` block.

`metadata/common.json` — shared defaults
```json
{
  "scope":  { "lob": "personal_auto", "domain": "personal_auto_policy_claims",
              "source_scope_mode": "SCHEMA_ALL_TABLES",
              "source_table_include_patterns": ["*"], "source_table_exclude_patterns": [],
              "source_object_types": ["TABLE"] },
  "source": { "catalog": "insurance_source_discovery", "schema": "gw_pc_bronze",
              "system_id": "guidewire_pc", "product": "PolicyCenter", "module": "", "version": "" },
  "output": { "catalog": "insurance_source_discovery", "schema": "control" },
  "knowledge_pack": { "pack_id": "public_us_pnc_personal_auto", "pack_version": "0.6.0",
                      "geography": "US_general", "pack_domains": ["policy", "claims"] },
  "profiling": { "policy_id": "GOV-001", "policy_version": "1.0.0", "run_mode": "METADATA_ONLY" },
  "contracts": { "set_version": "0.2.0" }
}
```

`metadata/sdd_param.json` — deployment overrides (win over common.json)
```json
{
  "models":   { "producer_endpoint": "REPLACE_PRODUCER", "critic_endpoint": "REPLACE_CRITIC" },
  "identity": { "workspace_host": "https://REPLACE.azuredatabricks.net",
                "execution_principal": "REPLACE_SP", "source_access_granted": "true" }
}
```

`metadata/README.md`: rules — grouped; `sdd_param.json` overrides `common.json`;
secrets never stored here; dynamic values are task-values; a second environment can
be added later as another override file without rework.

**Reconcile provisional artifacts** (created earlier — must not linger):
delete/replace `metadata/base.json` → `metadata/common.json`,
`metadata/prod.json` → `metadata/sdd_param.json`, delete `metadata/dev.json`,
delete top-level `src/agentic_data_modeler/job_params.py` and
`tests/unit/test_job_params.py` (recreate under the config subpackage below).

## 2. Loader — config subpackage (create)

`src/agentic_data_modeler/config/__init__.py` and
`src/agentic_data_modeler/config/job_params.py`:

- `load_params(repo_root, metadata_dir="metadata") -> dict` — read `common.json`,
  deep-merge `sdd_param.json` over it (override wins), strip `_comment`, return the
  nested dict. Fail closed if either file is missing.
- `resolve_job_params(dbutils, repo_root, *, dynamic_keys=()) -> dict` — call
  `load_params`, then for each key in `dynamic_keys` override with that widget value
  if non-empty. Returns the nested dict.
- `_deep_merge(base, override)` — recursive dict merge, ignore `_comment`.

Add `tests/unit/test_job_params.py` covering: deep-merge override, `load_params(ROOT)`
yields grouped keys from `common.json` merged with `sdd_param.json`, `_comment`
absent, missing file raises `FileNotFoundError`.

## 3. Refactor every job YAML (all jobs)

Jobs: `resources/source_discovery.job.yml` and every job invoking the analyze /
context / solution-run notebooks. For each task, replace the large repeated
`base_parameters` block with only:

```yaml
base_parameters:
  run_id: <task-prefix>_{{job.run_id}}
  # add ONLY the dynamic task-values this task consumes, e.g.:
  # source_tables: "{{tasks.discover_source_scope.values.source_tables}}"
  # source_snapshot_id: "{{tasks.snapshot_source_metadata.values.source_snapshot_id}}"
  # context_snapshot_id: "{{tasks.assemble_context.values.context_snapshot_id}}"
  # work_package_id: ${var.work_package_id}
```

In `databricks.yml`: drop the ~30 source/registration/pack variables. Keep
`resource_prefix`, `production_root_path`, and `work_package_id`. (No `env` variable —
single environment.)

## 4. Refactor every notebook (all workflows)

For each of: `validate_source_discovery_scope.py`, `discover_source_scope.py`,
`register_work_package.py`, `snapshot_source_metadata.py`, `profile_source.py`,
`assemble_source_evidence.py`, `assemble_context.py`, `register_solution_run.py`,
`analyze_source_dictionary.py`, `analyze_source_relationships.py`:

Replace the `PARAMS = (...)` widget block + `args = {p: dbutils.widgets.get(p)...}`
with:
```python
from agentic_data_modeler.config.job_params import resolve_job_params
for w in ("run_id", *DYNAMIC):            # DYNAMIC = this notebook's task-values
    dbutils.widgets.text(w, "")
params = resolve_job_params(dbutils, REPO_ROOT, dynamic_keys=("run_id", *DYNAMIC))
```
Then update every downstream read to the grouped path, e.g. `args["source_catalog"]`
→ `params["source"]["catalog"]`, `args["producer_endpoint"]` →
`params["models"]["producer_endpoint"]`. Where a notebook previously `json.loads`-ed a
list parameter (include/exclude patterns, object types, pack_domains), it now receives
a real list — remove the `json.loads`.

## 5. Remove `registration` end-to-end

- Delete `src/agentic_data_modeler/control/registration.py`; remove
  `RegistrationParameters` from `control/__init__.py` and any `workflow_state.py` use.
- In each workflow that used registration (`snapshot_source_metadata.py`,
  `discover_source_scope.py`, `profile_source.py`, `assemble_source_evidence.py`,
  `register_solution_run.py`): remove `RegistrationParameters.from_parameters(...)`,
  the `registration_mode`/`client_name`/`authorization_ref`/`effective_start_date`
  params, and the `registration.note` usage.
- Remove those params from the job YAML and `databricks.yml`.
- **SAFETY DECISION (do not silently drop):** the workflows also check
  `current_user()` == `execution_principal` and the workspace URL matches
  `workspace_host`. That is a real authorization guardrail. Keep it, but drive it from
  `params["identity"]["execution_principal"]` / `["workspace_host"]` /
  `["source_access_granted"]`. Remove only the *registration record/mode* concept, not
  the identity check — unless the owner explicitly says remove the identity check too.
  Stop and ask if unclear.

## 6. Contract JSON + DDL

- Identify any contract schema in `contracts/*.schema.json` carrying
  registration-derived fields (e.g. a `note`, `client_name`, `authorization_ref`,
  `registration_mode`, or an execution-identity field) — likely on `solution_run`,
  `work_package`, or `context_snapshot`. Remove those fields; if a removed field was
  required, drop it from `required`; bump that contract's `schema_version` per repo convention.
- Regenerate the affected DDL with the existing generator in `src/schema_builder/`
  (do not hand-edit `generated/ddl/**`; the files are marked auto-generated). Commit the regenerated `.sql`.
- Update any test fixtures / `test_contract_validation.py` referencing removed fields.
- Do NOT touch contracts unrelated to registration.

## 7. Mandatory validations (all must pass)

- `pip install -e ".[dev]" && pytest` — full suite green (Python 3.11).
- `databricks bundle validate -t <target>` passes.
- `grep -ri "registration\|RegistrationParameters\|registration_mode" src resources contracts` returns nothing meaningful.
- No `base.json` / `prod.json` / `dev.json` remain; only `metadata/common.json` + `metadata/sdd_param.json`.
- Every notebook imports `config.job_params.resolve_job_params` and reads grouped keys; no residual 30-key widget blocks.
- DDL under `generated/ddl/**` regenerated (not hand-edited), consistent with updated schemas.

## 8. Stop / escalation

- Stop if removing a registration field would break a contract the runtime agent
  (`analyst/*`) relies on — those must keep validating.
- Stop before removing the **identity authorization check** (§5) unless approved.
- Stop if the DDL generator entry point is unclear — do not hand-edit generated SQL.

## Acceptance

Params live only in `metadata/common.json` + `metadata/sdd_param.json` + task-values;
no `env` variable; registration gone (identity check retained via config unless told
otherwise); contracts + DDL regenerated; full test suite and `bundle validate` green.
