# Increment 1 Genie Code Build Handoff — Contracts

**Status:** Ready to build; integrity gate passed (`D23-13` `ACCEPTED`, 2026-07-16)
**Builder:** Genie Code
**Planner/specification owner:** Claude/Codex
**Contract owner:** this handoff, until Increment-1 schemas pass review

## 1. Builder mandate

Build the versioned JSON Schema contract suite, its deterministic validator, scaffolding/verification scripts, and tests for the Source Discovery and Source Data Dictionary flow — nothing else. Do not infer business meaning, invent vocabulary, approve any artifact, authorize a knowledge pack, or run an engagement. Contracts are created before their producers; no Increment-2+ producer code is in scope here.

If a governing document is missing, truncated, or contradictory, or if `contract_inventory.yaml` cannot be reconciled with this handoff, stop and raise a finding. Do not invent a schema to get past a gap.

## 2. Inputs Genie Code must read, in authority order

1. `docs/requirements/REQUIREMENTS_CHARTER.md`
2. `docs/architecture/AGENT_SOLUTION_ARCHITECTURE.md`
3. `docs/architecture/source-data-dictionary/SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md` and `SOURCE_DATA_DICTIONARY_AGENT_DESIGN.md`
4. `skills/author-source-discovery-contracts/SKILL.md`
5. `skills/author-source-discovery-contracts/references/contract_inventory.yaml` — the enumerated source of truth (31 records, `inventory_version: 0.2.0`)
6. `skills/author-source-discovery-contracts/references/contract_authoring_reference.md`
7. `skills/author-source-discovery-contracts/references/scaffolding_scripts_spec.md`
8. `skills/author-source-discovery-contracts/assets/_common.schema.json`, `record.schema.template.json`, `source_dictionary_attribute.example.schema.json`, `test_contracts.template.py`

No `D23-*` human decision applies to this increment — Increment 1 defines structure only, not source scope, profiling policy, or knowledge-pack approval. Do not wait on the decision register to start this build.

## 3. Build order

### Work package `I1-00` — Common schema

- Produce `contracts/_common.schema.json` at `$id: urn:agentic-data-modeler:contract:common:0.3.0` from the asset template.
- Define the contract-owned enums only: `evidence_state`, `provenance_class`, `confidence_components`, and the five lifecycle families (`lifecycle_material`, `lifecycle_append_only`, `lifecycle_operational`, `lifecycle_governance_decision`, `lifecycle_open_item`, `lifecycle_handoff`), plus `provenance`, `contextual_provenance`, `governed_code_ref`, `semantic_claim`, `material_approval_guard`, `handoff_issue_guard`, `no_op_guard`.
- **Exit:** passes JSON Schema Draft 2020-12 meta-schema validation; every enum in Reference §3–§4 is present and nowhere else.

### Work package `I1-01` — Scaffolding script S1

- Build `scaffold_contract.py` exactly to `scaffolding_scripts_spec.md` §S1: one record at a time from the inventory, template-copy without overwrite, token substitution (`RECORD_NAME`, `SCHEMA_VERSION`, `LIFECYCLE_FAMILY`, `PROVENANCE_DEF`, `LIFECYCLE_GUARD_DEF`), `x-authoring-status: TODO_RECORD_FIELDS` left in place, fixture stub emitted, unknown records/unresolved tokens/path escape refused.
- **Exit:** running S1 against all 29 inventory records produces 29 scaffolds with no path escape and no silent overwrite.

### Build increment `I1-02` — Record schema authoring (all 29 records)

Author each record schema from its S1 scaffold, grouped by family, removing `x-authoring-status: TODO_RECORD_FIELDS` only once fields, required fields, citations, and lifecycle guard are complete:

- **Control/run** (`produced_in: increment_1`): `engagement`, `work_package`, `solution_run`, `artifact_version`
- **Snapshots** (`produced_in: increment_2/3`, schema authored now): `source_snapshot`, `profile_snapshot`, `document_set`, `requirement_set`, `evidence_set`, `context_snapshot`
- **Evidence** (`produced_in: increment_2`): `evidence_item`, `source_object_observation`, `source_attribute_observation`, `profile_evidence`, `relationship_candidate`
- **Requirements** (`produced_in: increment_2`): `analytical_requirement`, `reporting_requirement`, `business_term`, `business_rule`
- **Dictionary** (`produced_in: increment_4`): `source_dictionary_object`, `source_dictionary_attribute`, `source_dictionary_relationship`, `source_dictionary_code_value` — use `contextual_provenance`, not base `provenance`
- **Governance** (`produced_in: increment_1`): `validation_finding`, `review_item`, `review_decision`, `open_question`
- **Lineage** (`produced_in: increment_1`): `artifact_dependency`, `lineage_edge`
- **Handoff/observability**: `source_dictionary_handoff` (`produced_in: increment_6`), `skill_resolution` (`produced_in: increment_1`)

Apply Reference §5–§6 for every record: `OBSERVED`/`INFERRED`/`DECIDED` require a typed value and matching evidence rule; `UNRESOLVED` requires `open_question_ref` and no value; `CODE_VALUE`/`KEY_ROLE`/`PRIVACY_CLASS`/`RETENTION_RULE` require `governed_code_ref`; root envelope schemas use `unevaluatedProperties: false`, self-contained objects use `additionalProperties: false`.

**Exit:** 31 `contracts/<record>.schema.json` files, each with a stable versioned `$id` matching the inventory pattern, no inline enum outside its record's `allowed_inline_enum_paths`, no domain vocabulary except via `governed_code_ref`.

### Work package `I1-03` — Verification scripts S2–S6 and runner

- Build `verify_inventory_complete.py`, `verify_ids_versions.py`, `verify_vocabulary_ownership.py`, `verify_inventory_relationships.py`, `verify_contract_behavior.py` exactly to `scaffolding_scripts_spec.md` §S2–§S6.
- Build `verify_contracts.py` to run S2–S6, schema meta-validation, and the full unit/integration suite, non-zero exit on any failure.
- **Exit:** all five verifiers plus the runner execute clean against the 31 authored schemas; each verifier independently fails when its target defect is injected (prove this with a deliberately broken fixture per script, then revert).

### Work package `I1-04` — Contract validator

- Build one validator in `src/agentic_data_modeler/contracts/validator.py` using `Draft202012Validator`, `FormatChecker`, and a `referencing.Registry` containing `_common.schema.json`, per Reference §7.
- After schema validation, recursively locate semantic claims and physical evidence references and verify: referenced evidence exists and validates; `OBSERVED`/physical references resolve to `SOURCE_FACT`; engagement/work-package identity match; `INFERRED` `evidence_count` equals unique evidence references; governed code references match the context-pack identity/version/fingerprint when context exists; approval/handoff decision references resolve and are applicable.
- No hard-coded claim-name list — walk the schema-declared `semantic_claim` and evidence-reference shapes generically.
- **Exit:** validator accepts every S6 positive fixture and rejects every S6 negative/mutation case with a specific, attributable error.

### Work package `I1-05` — Test suite

- Instantiate `assets/test_contracts.template.py` as the reusable structural/referential test base.
- Add at least one positive and one negative fixture per record (31×2 minimum), plus the S6 mutation-test set: wrong schema version, extra fields, unresolved authoring markers, observed/inferred/decided-without-value, unresolved-with-value, mismatched value discriminators, governed types without exact reference, inconsistent `INFERRED` evidence count, dangling/wrong-provenance/cross-engagement/cross-work-package evidence, material approval or issued handoff without an applicable decision.
- Forward-test at least one record from every lifecycle family: `evidence_item` (append_only), `work_package` (operational), `review_decision` (governance_decision), `open_question` (open_item), one material dictionary record, `source_dictionary_handoff` (handoff).
- **Exit:** full suite green under `pytest`; every family and every mutation case in `scaffolding_scripts_spec.md` §S6 is represented and passing.

### Work package `I1-06` — Build handoff evidence

- Assemble the completion evidence listed in §6 below and package it as one builder-handoff record.

## 4. Expected project placement

```text
contracts/
  _common.schema.json
  <record>.schema.json        # 31 files, one per inventory record
  scripts/
    scaffold_contract.py
    verify_inventory_complete.py
    verify_ids_versions.py
    verify_vocabulary_ownership.py
    verify_inventory_relationships.py
    verify_contract_behavior.py
    verify_contracts.py
src/agentic_data_modeler/
  contracts/
    __init__.py
    validator.py
tests/
  unit/contracts/
  fixtures/synthetic/contracts/
```

Do not place record validation logic anywhere else; `src/agentic_data_modeler/contracts/validator.py` is the single contract-validation boundary other increments must import, not duplicate.

## 5. Mandatory quality gates

- `pytest` passes for the full repository test suite, not just new tests.
- `verify_contracts.py` (S2–S6 + meta-validation + suite) exits zero.
- Exactly 31 record schemas plus `_common.schema.json`; no undeclared `*.schema.json` under `contracts/`.
- No schema contains `x-authoring-status: TODO_RECORD_FIELDS` or an unresolved scaffold token.
- No inline enum outside its record's `allowed_inline_enum_paths`; no domain vocabulary without `governed_code_ref`.
- `build_after` graph is acyclic; every reference target names an inventory record; Increment-2 evidence never requires an Increment-3 record.
- Nothing in this build approves an artifact, authorizes a knowledge pack, or changes `approval_state`/`runtime_eligible`.

## 6. Evidence Genie Code must return for review

- files changed, grouped by work package;
- `contract_inventory.yaml` version consumed and confirmation no record was added, removed, or reordered;
- `verify_contracts.py` output (S2–S6 individually, meta-validation, suite);
- test names and results, including every mutation/negative case from §S6;
- confirmation the integrity gate (Reference §8) was rechecked before and held during the build;
- unresolved decisions or contract gaps found while authoring; and
- a statement that no governing document, approval state, or runtime eligibility was changed.

## 7. Stop conditions

Stop and return a blocking finding when:

- `contract_inventory.yaml` record count, names, or dependency targets do not reconcile with this handoff;
- a structural term has no accepted contract owner in `_common.schema.json`;
- a domain code is needed but cannot resolve to an approved pinned pack version (leave it as a `governed_code_ref` placeholder finding, do not invent a value);
- a governing document fails the integrity gate;
- the build would require approving an artifact, authorizing a knowledge pack, or changing `approval_state`/`runtime_eligible`; or
- completing a test would require weakening a structural, provenance, or lifecycle rule in the reference material.
