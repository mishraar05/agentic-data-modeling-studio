---
name: author-source-discovery-contracts
description: >-
  Author or revise the versioned JSON Schema contract suite, deterministic
  validation specification, and tests for the Source Discovery and Source Data
  Dictionary flow. Use for Increment-1 contract design covering engagement,
  work-package, source snapshot, profiling, supplied evidence, analytical
  requirements, governed context, dictionary, review, lineage, handoff, and
  skill-resolution records. This is an authoring-plane skill; it does not infer
  business meaning, approve artifacts, authorize knowledge packs, or run an
  engagement.
---

# Author Source Discovery Contracts

## Status and boundary

Version: `0.3.1-DRAFT`  
Status: `DRAFT / READY_FOR_AUTHORING_USE`

Use this Skill to turn intact governing requirements and designs into contract
specifications that Genie Code or an engineer can implement. Do not use it as a
runtime source-analysis agent.

The repository's controlling architecture document has been restored and its
integrity gate passes. This Skill may now guide Increment-1 contract authoring.
Generated contracts remain `DRAFT` until their schemas, validators and evaluation
results pass normal architecture review and human-governance gates.

The responsibility split is fixed:

- Claude/Codex: analyze governing material, author or revise this Skill and its
  specifications, and identify unresolved decisions.
- Genie Code or an engineer: create production schemas, validation code,
  scaffolding utilities, and automated tests from the accepted specification.
- Humans: approve architecture, privacy and profiling policy, controlled
  vocabularies, runtime eligibility, lifecycle transitions, and exceptions.

## Integrity gate

Before authoring or changing a contract:

1. Read `AGENTS.md` completely.
2. Read the Requirements Charter and controlling architecture completely.
3. Read both Source Data Dictionary design documents completely.
4. Confirm that every governing file ends normally and has no truncation or
   binary corruption.
5. If any controlling document is incomplete, stop authoritative work, record
   the exact defect, and keep all proposed artifacts explicitly draft.

Do not infer missing policy, widen scope, or change an approval state to get past
this gate.

## Resources to load

After the integrity gate, load only the resources needed for the task:

- `references/contract_inventory.yaml`: machine-readable record inventory,
  lifecycle family, schema version, authoring dependencies, instance-reference
  requirements, and permitted inline-enum paths.
- `references/contract_authoring_reference.md`: contract invariants, vocabulary
  ownership, provenance, semantic-claim, lifecycle, and validator rules.
- `references/scaffolding_scripts_spec.md`: deterministic S1-S6 builder
  specification and required forward tests.
- `assets/_common.schema.json`: reusable structural vocabulary and guards.
- `assets/record.schema.template.json`: neutral per-record scaffold.
- `assets/source_dictionary_attribute.example.schema.json`: one worked material
  record; use for pattern inspection, not as a universal template.
- `assets/test_contracts.template.py`: reusable structural and referential tests.

Treat `contract_inventory.yaml` as the enumerated source of truth. Prose explains
semantics but must not silently add, remove, or reorder records.

## Non-negotiable model

Preserve these distinctions:

- `build_after` is schema authoring order only.
- `required_instance_refs` and `optional_instance_refs` describe runtime record
  relationships.
- `OBSERVED`, `INFERRED`, `DECIDED`, and `UNRESOLVED` are contract-owned trust
  states.
- Domain codes, privacy classes, retention rules, jurisdictions, products, and
  other business vocabularies are knowledge-pack-owned and referenced by a
  pinned `governed_code_ref` containing pack id, pack version, code-set id,
  fingerprint, and code.
- Raw source facts require `SOURCE_FACT` evidence. Supplied documents and
  analytical requirements remain distinguishable evidence classes.
- A context snapshot may govern downstream interpretation, but evidence captured
  before context assembly must not require a context snapshot.
- Profiling evidence is optional wherever profiling policy permits metadata-only
  or restricted execution.
- Material approval and handoff issuance are human-governed lifecycle events.

## Authoring workflow

1. Run the integrity gate and identify the controlling document versions.
2. Reconcile the requested scope with the machine inventory. Do not proceed if
   record count, names, dependency targets, or lifecycle family are inconsistent.
3. Resolve structural vocabulary through `_common.schema.json`. Add business
   vocabularies only as governed references, never as invented enums.
4. Scaffold each record from the neutral template using deterministic token
   substitution. Remove the authoring marker only after the record-specific
   properties, required fields, provenance form, and lifecycle guard are defined.
5. Keep authoring order separate from instance dependency checks. Reject cycles
   in `build_after`; reject unknown required or optional reference targets.
6. Apply the correct provenance form. Use contextual provenance only for records
   produced after governed context assembly.
7. Represent semantic meaning with `semantic_claim`. Enforce its value
   discriminator, evidence requirements, confidence components, governed-code
   requirements, and unresolved-question rules.
8. Add deterministic structural validation and generic referential validation.
   Referential checks must walk nested claims and physical evidence references;
   they must not depend on a hard-coded list of field names.
9. Evaluate at least one positive and one negative fixture for every lifecycle
   family, plus cross-engagement, cross-work-package, dangling evidence,
   provenance-class, typed-value, and degraded-mode cases.
10. Produce a build handoff that lists generated files, inventory version, common
    schema version, unresolved decisions, integrity-gate status, and test results.

## Schema rules

- Use JSON Schema Draft 2020-12 and stable versioned `$id` values.
- Pin every shared `$ref` to the common schema version.
- Close record and nested object shapes; do not use arbitrary objects as an
  escape hatch for values or mappings.
- Require the common envelope and the inventory-selected lifecycle state,
  provenance definition, and lifecycle guard.
- Require at least one supporting evidence item for `OBSERVED`, `INFERRED`, and
  `DECIDED` claims. `UNRESOLVED` requires a question and carries no asserted
  value.
- Match `value_type` to the JSON representation. Governed code-bearing types
  require a pinned governed-code reference.
- Enforce same-engagement and same-work-package scope for referenced evidence.
- Keep records append-only where the inventory says append-only; supersede or
  version material artifacts instead of overwriting them.

## Fail-closed conditions

Stop and return a blocking finding when:

- a governing document is missing, truncated, corrupt, or contradictory;
- inventory count or dependencies do not reconcile;
- a structural term has no accepted contract owner;
- a domain code cannot resolve to an approved pinned pack version;
- a reference is dangling or crosses engagement/work-package scope;
- an observed fact lacks `SOURCE_FACT` evidence;
- a lifecycle transition lacks the required human decision;
- profiling is required despite a permitted metadata-only or restricted mode;
- the requested action would approve an artifact or authorize a knowledge pack.

## Completion evidence

A draft authoring package is complete only when:

- the Skill package passes the Skill validator;
- the inventory count, references, and authoring graph pass deterministic checks;
- common and worked-example schemas pass Draft 2020-12 meta-schema validation;
- all lifecycle-family forward tests pass;
- the reusable contract test template passes in an isolated fixture repository;
- the build handoff explicitly reports the governing-document integrity status.

Passing these checks does not make the package production-approved. Authoritative
publication remains a human architecture decision after the controlling
architecture is restored.

## Changelog

- `0.3.1-DRAFT`: cleared the architecture-truncation blocker after verifying the
  restored controlling document; retained draft publication and human-review
  gates.
- `0.3.0-DRAFT`: expanded the inventory to cover Increment 2-3 inputs and lineage;
  separated authoring and instance dependencies; corrected evidence/context and
  optional-profiling semantics; hardened typed values, governed references,
  lifecycle guards, generic referential validation, packaging, and evaluation.
- `0.2.0-DRAFT`: introduced contract-owned trust vocabulary, lifecycle families,
  machine-readable inventory, and two-tier tests.
