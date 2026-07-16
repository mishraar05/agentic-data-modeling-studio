# Deterministic Scaffolding and Validation — Genie Code Specification

The planner owns this specification; Genie Code builds the scripts. Scripts contain no business semantics and return machine-readable findings with non-zero exit on failure.

## S1 — `scaffold_contract.py`

- Accept exactly one record from `contract_inventory.yaml`.
- Copy `assets/record.schema.template.json` without overwriting an existing schema.
- Substitute `RECORD_NAME`, `SCHEMA_VERSION`, `LIFECYCLE_FAMILY`, `PROVENANCE_DEF` and `LIFECYCLE_GUARD_DEF` from inventory policies.
- Leave `x-authoring-status: TODO_RECORD_FIELDS`; never pretend the scaffold is complete.
- Emit a fixture stub tagged with the exact record name and lifecycle family.
- Refuse unknown records, unresolved tokens and path escape.

## S2 — `verify_inventory_complete.py`

- Assert `expected_record_count` equals the unique record count.
- Require exactly one `contracts/<record>.schema.json` per inventory record.
- Exempt only `contracts/_common.schema.json` from the record inventory.
- Reject every other undeclared `*.schema.json`.
- Fail while any schema contains `x-authoring-status: TODO_RECORD_FIELDS` or unresolved scaffold tokens.
- Require at least one positive and one negative fixture tagged to each record.

## S3 — `verify_ids_versions.py`

- Validate every `$id` against the inventory record and version.
- Validate every `schema_version` const.
- Reject duplicate `$id` values.
- Require every common `$ref` to match `common_ref`.
- Validate SHA-256 fields with the contract pattern.

## S4 — `verify_vocabulary_ownership.py`

- Permit contract-owned enums only in `_common.schema.json`.
- For a record-schema inline enum, require its JSON Pointer in that record's `allowed_inline_enum_paths`.
- Reject a record-schema inline enum that is not allow-listed; do not guess whether an enum is “domain” from its words.
- Require domain-vocabulary fields to use `governed_code_ref` and reject copied pack values.
- Reject copied envelope fields and a root `additionalProperties: false` where `unevaluatedProperties: false` is required.

## S5 — `verify_inventory_relationships.py`

- Require every `build_after`, required reference and optional reference to name an inventory record.
- Require the `build_after` graph to be acyclic.
- Do not reject cycles in instance references; approval and supersession relationships may be bidirectional by design.
- Enforce the sequencing invariant: records produced in Increment 2 cannot require an Increment-3 record.
- Enforce permitted degraded modes: `profile_evidence` cannot be a required reference of `source_dictionary_attribute`.

## S6 — `verify_contract_behavior.py`

Run mutation tests proving that contracts reject:

- wrong schema version, extra fields and unresolved authoring markers;
- observed/inferred/decided claims without values;
- unresolved claims that assert values;
- mismatched value discriminators;
- governed value types without exact governed references;
- inferred evidence count zero or inconsistent with references;
- dangling, wrong-provenance, cross-engagement and cross-work-package evidence; and
- material approval or issued handoff without applicable decisions.

Forward-test at least one record from every lifecycle family: evidence item, work package, review decision, open question, material dictionary record and handoff.

## Runner

`verify_contracts.py` runs S2–S6, schema meta-validation and the full unit/integration test suite. Green proves structural completeness and deterministic integrity only; it never proves semantic accuracy.
