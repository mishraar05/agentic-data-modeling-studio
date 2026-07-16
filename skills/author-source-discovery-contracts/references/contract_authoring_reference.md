# Contract Authoring Reference — Increment 1

Use this reference with `contract_inventory.yaml`, `scaffolding_scripts_spec.md` and the `assets/` templates. The Requirements Charter wins on conflict.

## 1. Contract coverage

`contract_inventory.yaml` is the only machine-readable inventory. It contains 31 records covering:

- control/run plus source, profile, document, requirement, evidence and context snapshots/sets;
- source observations, profile evidence and relationship candidates;
- supplied/extracted requirements, business terms and business rules;
- Source Data Dictionary object, attribute, relationship and code-value artifacts;
- findings, review items, decisions and open questions;
- artifact dependency and lineage edges; and
- approved dictionary handoff and skill-resolution evidence.

This closes the handoff requirement for source/profile/evidence/requirement/context IDs and the Charter §5.2 requirement records.

## 2. Dependency semantics

Do not treat one overloaded dependency list as both build order and runtime cardinality.

| Inventory field | Meaning |
|---|---|
| `build_after` | Acyclic schema-authoring order only |
| `required_instance_refs` | Record types every persisted instance must reference, subject to its approved contract |
| `optional_instance_refs` | Applicable references that must remain optional in permitted degraded modes |

Important consequences:

- Increment-2 evidence never requires an Increment-3 `context_snapshot`.
- `profile_evidence` is optional for dictionary attributes when `METADATA_ONLY` mode is authorized.
- Context-dependent dictionary artifacts use `contextual_provenance`; pre-context evidence uses base `provenance`.

## 3. Vocabulary ownership

Contract-owned structural invariants live only in `assets/_common.schema.json`:

- `evidence_state`: `OBSERVED`, `INFERRED`, `DECIDED`, `UNRESOLVED`;
- `provenance_class`: `SOURCE_FACT`, `DOCUMENT_CLAIM`, `GOVERNED_INPUT`, `REQUIREMENT`, `INFERENCE`, `HUMAN_DECISION`, `UNRESOLVED`;
- confidence components; and
- lifecycle families.

Domain vocabulary—party roles, coverage families, privacy classes and code meanings—uses `governed_code_ref`. It pins `pack_id`, `pack_version`, `code_set_id`, a SHA-256 fingerprint and the selected code.

## 4. Lifecycle policy

| Lifecycle family | Values | Guard |
|---|---|---|
| `material` | `DRAFT`, `APPROVED`, `REJECTED`, `SUPERSEDED` | `APPROVED` requires `review_decision_ref` |
| `append_only` | `COMMITTED`, `SUPERSEDED` | no human approval |
| `operational` | `ACTIVE`, `CLOSED`, `REJECTED`, `SUPERSEDED` | workflow state remains a separate controlled field |
| `governance_decision` | `RECORDED`, `SUPERSEDED` | the record is the decision; no recursive approval |
| `open_item` | `OPEN`, `RESOLVED`, `SUPERSEDED` | resolution is decision-driven |
| `handoff` | `DRAFT`, `ISSUED`, `REVOKED`, `SUPERSEDED` | `ISSUED` requires decision reference and fingerprint |

## 5. Semantic claims

Use `_common.schema.json#/$defs/semantic_claim` and preserve these rules:

- `OBSERVED`, `INFERRED` and `DECIDED` require a typed value.
- `UNRESOLVED` requires `open_question_ref` and must not assert a value.
- `OBSERVED` requires evidence that resolves to `SOURCE_FACT`.
- `INFERRED` requires unique evidence references and confidence with `evidence_count >= 1`; the validator confirms the count equals unique references.
- `DECIDED` requires `review_decision_ref`.
- `LIST`, `MAPPING` and `CARDINALITY` values use their closed structural shapes.
- `CODE_VALUE`, `KEY_ROLE`, `PRIVACY_CLASS` and `RETENTION_RULE` require `governed_code_ref`.

Physical observations carry their own unique `evidence_refs`. Dataset validation verifies existence, `SOURCE_FACT` provenance, same engagement and same work package.

## 6. Schema conventions

- JSON Schema Draft 2020-12.
- `$id`: `urn:agentic-data-modeler:contract:<record>:<version>`.
- Per-record `schema_version` is a `const` matching the inventory.
- Root schemas that reuse the envelope use `unevaluatedProperties: false`.
- Self-contained objects use `additionalProperties: false`.
- Use the neutral asset for scaffolding and the attribute example only as a worked example.
- Remove `x-authoring-status: TODO_RECORD_FIELDS` only after record fields, required fields, citations and lifecycle guard are complete.

## 7. Validator obligations

Genie Code builds one contract validator using `Draft202012Validator`, `FormatChecker` and a `referencing.Registry` containing `_common.schema.json`.

After schema validation it must recursively locate semantic claims and physical evidence references and verify:

- referenced evidence records exist and validate;
- observed and physical references resolve to `SOURCE_FACT`;
- engagement and work-package identities match;
- inferred `evidence_count` equals the number of unique evidence references;
- governed code references match the selected context-pack identity/version/fingerprint when context exists; and
- approval/handoff decision references resolve and are applicable.

No hardcoded claim-name list is permitted.

## 8. Integrity and stop conditions

Before authoring, verify that every governing document exists, is text-readable, contains the cited sections and does not end mid-sentence. Stop if integrity fails. The controlling `AGENT_SOLUTION_ARCHITECTURE.md` was restored and verified on 2026-07-16; future integrity failures still block authoring.

Do not modify governing documents, knowledge packs, registries, approval state or runtime eligibility from this Skill.
