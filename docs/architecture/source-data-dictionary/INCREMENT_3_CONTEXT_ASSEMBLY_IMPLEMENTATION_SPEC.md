# Increment 3 — Governed Context Assembly Implementation Specification

**Status:** Draft implementation specification for human and architecture review  
**Builder:** Genie Code  
**Planning authority:** Claude/Codex  
**Human authority:** knowledge approval/authorization, effective-date policy and acceptance thresholds  
**Governing requirements:** `docs/requirements/REQUIREMENTS_CHARTER.md`  
**Controlling design:** `AGENT_SOLUTION_ARCHITECTURE.md` §4 and `SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md` §§6, 9–10, 18–19  
**Contract dependency:** Increment-1 `work_package`, `context_snapshot`, evidence, decision and version contracts

## 1. Outcome and boundary

Increment 3 reproducibly transforms one `EVIDENCE_READY` work package into one immutable, contract-valid `CONTEXT_READY` snapshot. It selects the smallest authorized combination of:

- work-package scope and policies;
- Increment-2 source evidence and supplied requirements;
- an exact approved/runtime-eligible knowledge-pack version;
- applicable prior approved human decisions;
- unresolved contradictions/questions; and
- exact task, contract, prompt, skill, tool and budget declarations.

This is deterministic context engineering. It does not invoke the Source Data Analyst, interpret source meaning, run a modeling skill, approve knowledge, repair evidence, or create dictionary records.

## 2. Preconditions and hard gates

The assembler must fail closed unless all are true:

1. the work package is authorized and exactly `EVIDENCE_READY`;
2. the requested source/evidence/profile snapshots exist, validate and remain in scope;
3. the requested knowledge-pack identity and version are registered exactly once;
4. both registry and manifest are `APPROVED` and `runtime_eligible: true`;
5. pack scope, effective date, authorization and fingerprints match the request;
6. every included prior decision is approved, applicable, unexpired and from the same engagement/scope;
7. the output contract, tool policy and budget versions exist; and
8. there is no unresolved blocking conflict among required inputs.

The current project has no runtime-eligible pack. Genie Code may build and test all negative gates now, but no project candidate pack may be promoted or copied into a positive runtime path. Positive integration testing requires a separately authorized synthetic fixture or a human-approved project pack.

## 3. Durable task graph

```text
verify_evidence_ready
  -> select_authorized_knowledge
  -> resolve_prior_decisions
  -> resolve_task_evidence
  -> assemble_context_snapshot
  -> validate_context_ready
```

| Task | Output | Gate |
|---|---|---|
| `verify_evidence_ready` | pinned work-package/evidence/profile/document/requirement versions | all Increment-2 references and fingerprints valid |
| `select_authorized_knowledge` | exact pack/module/asset selection and authorization result | exact approved/runtime-eligible, effective and scoped content only |
| `resolve_prior_decisions` | applicable decision set and supersession/conflict result | approved, same engagement/scope, valid time and no unresolved collision |
| `resolve_task_evidence` | minimal evidence IDs grouped by object/task and provenance class | every reference authorized, available and non-stale |
| `assemble_context_snapshot` | immutable context manifest, content index and hash | deterministic ordering, budgets and all dependencies recorded |
| `validate_context_ready` | validation summary and `CONTEXT_READY` transition | contract, reference, scope, authorization, conflict and fingerprint checks pass |

## 4. Context request

The request is created from the authorized work package and Increment-1 contracts. It must identify:

- engagement, work package, LOB, domain, source system and exact object/attribute slice;
- task ID/type and versioned output contract;
- source, profile, document, evidence and requirement-set snapshot IDs;
- exact requested pack ID/version, geography/jurisdiction, product/module/version and effective date;
- prior-decision selection timestamp;
- allowed evidence and knowledge classes;
- required and optional context sections;
- prompt/skill/tool policy versions, even when no skill is activated yet;
- token/record/byte budgets per section and overall; and
- requested context-schema version.

No free-form prompt may expand the authorized scope.

## 5. Knowledge selection

The existing `select_approved_pack` implementation is a useful repository gate but is not sufficient for Increment 3. Genie Code must extend the runtime selection service to validate:

- caller/work-package authorization for the pack and content classes;
- effective-from/effective-to applicability at the requested date;
- jurisdiction, product/module/version and domain applicability where declared;
- registry, manifest, module and asset fingerprints;
- lifecycle/supersession and revocation state;
- selected module dependencies and prohibited combinations; and
- the exact governed content representation used at runtime, not only the portable repository manifest.

Selection is exact. There is no “latest”, nearest-scope, directory-scan or candidate fallback. If more than one version or precedence path is applicable, emit a conflict and stop.

Only selected modules/assets enter the context index. Loading the whole pack merely because it is approved violates the minimum-context requirement.

## 6. Evidence and decision selection

### Evidence classes remain distinct

`SOURCE_FACT`, `DOCUMENT_CLAIM`, `GOVERNED_INPUT`, `REQUIREMENT`, `INFERENCE`, `HUMAN_DECISION` and `UNRESOLVED` must never be flattened into a generic “context” class.

There is no single global evidence ranking because authority depends on the question:

- physical source state is established by authorized source facts;
- stated analytical intent is established by supplied requirements;
- portable terminology/standards come from governed inputs;
- engagement-specific semantic choices come from applicable approved human decisions;
- document claims establish what a document says, not what the source physically contains; and
- inferences remain candidates regardless of confidence metadata.

When two items of the same authority conflict, retain both, create a contradiction reference and stop if the conflict is blocking. A human decision may settle interpretation but must not rewrite or erase a contrary physical source fact.

### Decision applicability

Include a decision only when all applicable dimensions match: engagement, LOB, domain, source system, object/attribute or artifact scope, effective time and non-superseded status. Preserve the complete supersession chain and rationale reference.

## 7. Minimum-context algorithm

For each requested task/object slice, assemble in this order:

1. scope lock, task objective, output contract and policies;
2. object/attribute inventory and physical observations;
3. task-relevant profiles and relationship evidence;
4. cited document/report/requirement evidence explicitly linked to the slice;
5. applicable approved human decisions and unresolved contradictions;
6. the smallest applicable governed glossary/domain/code-set/privacy/standard modules; and
7. prompt/skill/tool declarations and execution budgets.

The selector must use explicit references, scope fields and typed retrieval rules. Vector/semantic search may retrieve authorized unstructured candidates, but every returned item must pass deterministic post-filtering before inclusion.

When a section exceeds budget:

- retain identifiers, provenance, contradictions and high-authority items;
- use a versioned deterministic reduction for structured statistics;
- use a versioned summarizer only where authorized;
- preserve source evidence IDs and summary-to-source coverage; and
- stop rather than omit a required blocking item.

Token budget cannot be enforced only after prompt rendering; record and byte limits must also protect retrieval and persistence.

## 8. Context snapshot and fingerprint

The snapshot is a manifest and index, not an unstructured prompt dump. It must record, subject to the Increment-1 contract:

- context snapshot, work-package and run identity;
- requested scope and task/output-contract version;
- exact IDs, versions and fingerprints of evidence/profile/document/requirement sets;
- exact pack, module, asset and governed-content IDs/versions/fingerprints;
- included prior decisions, contradictions and open questions;
- prompt, skill, tool, model policy and budget versions;
- authorization and policy-decision references;
- retrieval queries/rules and selected item IDs;
- omitted/suppressed item counts with reasons;
- canonicalization/fingerprint algorithm version;
- created time, lifecycle state and validation result; and
- content hash over canonical ordered references plus policy/configuration versions.

Canonicalization must define stable key ordering, list ordering, timestamps and null handling. The same immutable inputs and algorithm version must produce the same fingerprint. Model-generated summaries may vary; when used, their model/prompt version and output hash become explicit snapshot inputs rather than being hidden behind the same fingerprint.

## 9. Authorization and isolation

- Enforce access with Unity Catalog privileges and solution policy middleware; prompt filters are not security controls.
- Constrain every read to the engagement/work-package identity and selected evidence class.
- Prefer centrally governed row-filter/column-mask or ABAC policies for repeated isolation rules; do not bypass them for profiling or retrieval.
- Never include raw protected values when minimized evidence satisfies the task.
- Do not index protected documents into AI Search unless a separately authorized minimized index and row/object filter strategy exist.
- Validate authorization again when materializing the final snapshot, not only when the work package was registered.
- Record only policy decision references; never persist credentials or entitlement tokens.

## 10. Staleness, conflict and invalidation

The snapshot becomes invalid for new execution when any pinned dependency is revoked, superseded, changed, expired or inaccessible. Existing historical snapshots remain immutable and auditable.

| Condition | Result |
|---|---|
| evidence/profile fingerprint mismatch | block; require a new Increment-2 snapshot |
| pack revoked, candidate, expired or fingerprint mismatch | block; no fallback |
| cross-engagement decision/evidence | security finding; block |
| required content omitted by budget | block |
| non-blocking contradiction | retain both sides and explicit impact/permission |
| blocking contradiction | `NEEDS_INPUT`; no `CONTEXT_READY` |
| changed contract/policy/selector version | create a new context snapshot |
| same immutable inputs and versions | return existing snapshot idempotently |

Dependency invalidation must be queryable so later dictionary artifacts can identify which context change made them stale.

## 11. Acceptance and evaluation

| Test | Required result |
|---|---|
| candidate or non-runtime pack | fail closed |
| missing/duplicate exact pack version | fail closed |
| correct pack but wrong LOB/domain/jurisdiction/effective date | fail closed |
| registry/manifest/module fingerprint mismatch | fail closed |
| unauthorized governed module | excluded and blocking if required |
| cross-engagement evidence or decision | security failure |
| superseded decision | excluded; superseding chain retained |
| document claim contradicts source fact | both retained, classes distinct, conflict raised |
| context over budget | deterministic reduction or explicit failure; never silent truncation |
| repeated identical request | same snapshot/fingerprint and no duplicate persistence |
| one dependency/version changes | new snapshot and invalidation edge |
| log/trace inspection | no credentials or prohibited raw values |
| authorized proof slice | agreed completeness, latency, cost and reproducibility thresholds pass |

Before pack approval, positive-path tests must use isolated synthetic registries/manifests and must never alter `knowledge/registry/pack_registry.yml` or a project pack’s approval fields.

## 12. Builder deliverables

After Increment-1 contracts are approved, Genie Code should produce:

1. a typed context-request/selection/manifest implementation bound to those contracts;
2. exact knowledge, evidence, requirement and prior-decision selectors;
3. authorization, applicability, effective-date, conflict and fingerprint middleware;
4. immutable context snapshot/index persistence and dependency invalidation;
5. Lakeflow tasks and job-parameter wiring for the graph in §3;
6. unit, integration, security, idempotency and adversarial retrieval tests; and
7. MLflow/Delta operational evidence for selection counts, exclusions, budgets, cost and latency.

## 13. Current official Databricks references

- [Declarative Automation Bundles variables](https://docs.databricks.com/aws/en/dev-tools/bundles/variables)
- [Configure job parameters](https://docs.databricks.com/aws/en/jobs/job-parameters)
- [Unity Catalog row filters and column masks](https://docs.databricks.com/aws/en/data-governance/unity-catalog/filters-and-masks)
- [Create and manage ABAC policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies)
