# Source Data Dictionary Agent — Design

**Status:** Draft component design (elaborates `AGENT_SOLUTION_ARCHITECTURE.md` §2 "Source Data Analyst" capability)
**Parent source-discovery flow:** [`SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md`](SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md)  
**Governing documents:** `docs/requirements/REQUIREMENTS_CHARTER.md` §3–§5 (scope, contract), `docs/architecture/AGENT_SOLUTION_ARCHITECTURE.md` §1–§6 (LLM/code split, context, guardrails, harness)
**Anti-drift gate:** Advances the Reconstructed Source Data Dictionary deliverable (Charter §5.1). Applies to any selected LOB/domain slice — the design itself is reusable; only the context envelope is scope-specific. Acceptance evidence is Charter §5.1's quality gates and §7's Source Data Dictionary coverage/quality measures. This belongs now because `contracts/README.md` requires contracts before producers, and this agent is the first producer the project needs — the knowledge layer and jurisdiction decision it depends on already exist.

This is a design for review, not an approved contract. No code or schema in this document is authoritative until the corresponding JSON Schema contracts under `contracts/` are written and validated, per project convention.

## 1. What it is, and what it is not

The Source Data Dictionary (SDD) Agent is one specialist capability inside the single custom agent harness (Architecture §2) — not a separately deployed agent. It reconstructs source meaning, structure, relationships, code values, evidence, and gaps for every in-scope source object and attribute in one bounded work package (one engagement, one LOB/domain, one allow-listed source boundary).

It does not: invent a business meaning without evidence, generate the Silver or Gold model, decide approval, or write back to governed knowledge. Those belong to later specialists (Silver ODS Modeler, Gold Dimensional Modeler, Review Coordinator) or to human reviewers.

## 2. Inputs

| Input | Source | Nature |
|---|---|---|
| Scope and identity | `context_snapshot` from the Scope and Context Manager | run ID, LOB, domain, source catalog/schema, frozen source manifest |
| Source catalog/schema/table/column/key/constraint/index/view metadata | Unity Catalog / information-schema, read via allow-listed tool | Deterministic, authoritative source fact |
| Approved source profiles | Profile store or a policy-bounded profiling job | Deterministic: null/distinct stats, value distributions, formats, ranges, patterns |
| Existing source dictionaries / design docs, if supplied | Evidence adapter (e.g. `ai_extract` with citations) | Structured claims with provenance, treated as untrusted document content until cited |
| Supplied report inventory and report-to-source knowledge, if in scope | Evidence adapter | Lineage evidence for business-meaning inference |
| Governed knowledge pack (approved version only) | `select_approved_pack` — glossary, code sets, standards, jurisdiction extension | Fail-closed; only APPROVED + runtime_eligible packs are ever admitted |
| Prior approved decisions for this engagement/object | `review_decision` Delta records | Durable context; takes precedence over background knowledge |
| Human answers to unresolved questions | `open_question` / `review_decision` | Closes prior UNRESOLVED items before re-analysis |

Everything the agent is allowed to see arrives as one bounded **context envelope** (Architecture §4.1) assembled before the call — it never scans directories or pulls whole repositories.

## 3. Flow

The flow alternates deterministic phases (code: exact facts, structure, validation) and LLM phases (semantic judgment, evidence-cited inference), per Architecture §1's split. Nothing semantic is ever hard-coded to an expected answer; nothing deterministic is ever left to model judgment.

```
Phase 0  Scope & context assembly           [deterministic]
Phase 1  Evidence ingestion                  [deterministic]
Phase 2  Relationship-candidate detection    [deterministic]
Phase 3  Object-level semantic analysis      [LLM]
Phase 4  Attribute-level semantic analysis   [LLM]
Phase 5  Contradiction & gap detection       [deterministic + LLM critic]
Phase 6  Confidence scoring                  [deterministic]
Phase 7  Contract validation                 [deterministic, fail-closed]
Phase 8  Human review checkpoint             [human + deterministic state machine]
Phase 9  Persistence & downstream generation [deterministic]
```

**Phase 0 — Scope and context assembly.** Validates run parameters the same way `src/workflows/00_validate_scope.py` already does (no placeholders, no unsafe identifiers, allow-listed tables only). Resolves the exact approved knowledge pack version through the fail-closed registry logic already built in `agentic_data_modeler.knowledge`. Pulls prior approved decisions for this engagement/object scope. Produces the context envelope and a `context_snapshot` record.

**Phase 1 — Evidence ingestion (code, not the model).** Pulls catalog/schema/table/column/key/constraint/index/view metadata and approved profiles for the allow-listed source_tables only, through read-only tools. Normalizes into `source_object_observation`, `source_attribute_observation`, `profile_evidence`, and `evidence_item` records. These are facts, not interpretations — nothing here has passed through the model yet, matching the charter's requirement to separate source fact from inference.

**Phase 2 — Relationship-candidate detection (code).** Declared constraints are authoritative. Undeclared candidates come from deterministic heuristics: naming-convention matches, datatype/domain compatibility, and cardinality signals from profiling (uniqueness, value-overlap). Because pairwise candidate generation across the allow-listed tables is combinatorial (worst case O(columns²)) and naming/type heuristics are individually low-precision, each candidate carries a deterministic support score and candidates below a configured threshold are recorded but suppressed from the LLM and review queues (still auditable, never silently dropped). Each surfaced candidate is written as a `relationship_candidate` with `validation_status: declared | heuristic_candidate`, its support score, and its supporting evidence — the LLM phases below add business meaning to these, they don't discover new ones from nothing.

**Phase 3 — Object-level semantic analysis (LLM).** For each in-scope object, the agent receives its evidence bundle (columns, keys, profile summary, any existing-doc fragments, report linkage) plus the scoped governed glossary/domain knowledge and prior decisions for that object. It proposes a candidate business name, purpose, subject area, and synonyms — each tagged with the contract-owned `evidence_state` structural vocabulary: `OBSERVED` (directly present in source evidence), `INFERRED` (a candidate conclusion supported by cited evidence), `DECIDED` (established by an authorized human decision), or `UNRESOLVED` (evidence insufficient or contradictory). Domain vocabulary remains knowledge-pack-owned and is referenced by exact pack/version/code-set/fingerprint. Anything not `OBSERVED` must cite its support: `INFERRED` cites `evidence_item` IDs, `DECIDED` cites the governing `review_decision`. Insufficient evidence must produce `UNRESOLVED` plus an `open_question`, never a guess — this is a hard prohibition, enforced again deterministically in Phase 7.

**Phase 4 — Attribute-level semantic analysis (LLM).** Same discipline per attribute: business name, definition, purpose, synonyms, lifecycle meaning. Coded/enumerated attributes get candidate value meanings from profile value distributions cross-referenced against governed code sets, with unmapped values flagged via `unknown_handling_state` rather than invented. Key-bearing attributes get business meaning added to the Phase 2 structural candidate — meaning never substitutes for structural evidence. Attributes that look privacy-sensitive (name/address/DOB/government-ID patterns) get a candidate sensitivity classification citing governed privacy guidance, always routed to `privacy_steward` review — the agent never finalizes a privacy class.

**Phase 5 — Contradiction and gap detection.** A deterministic pass checks every proposed definition against the governed glossary for term conflicts, against prior approved decisions for supersession conflicts, and against the object/attribute inventory for coverage gaps. A separate LLM critic pass, run against an independently phrased rubric (not the same prompt that produced the definitions), challenges plausibility, evidence sufficiency, and cross-object consistency (e.g., the same column name defined two different ways in two tables). Rephrasing the rubric alone does not make the critic independent: a critic sharing the producer's model and context envelope inherits its blind spots, so critic-pass agreement is treated as correlated, not independent, confirmation. Where the harness's approved model list allows, the critic should run on a different model and receive a reduced context, and residual correlated-error risk is accepted rather than assumed away. Anything unresolved becomes an `open_question`, not a silent default.

**Phase 6 — Confidence scoring (deterministic).** Confidence is reported as its components — evidence type (declared constraint > profiling statistic > glossary match > single LLM inference), evidence count, and critic-pass agreement — not collapsed into a single opaque score. The weighting across those components is a hand-authored heuristic *prior*, not a calibrated probability: it expresses which evidence the project trusts more, and it must not be tuned against any evaluation set (Architecture §1 prohibits encoding answer keys). Its numeric output therefore carries no validated accuracy meaning until it is calibrated against the unseen, independently labelled cases required by Charter §7; the design treats calibration of this function as a required acceptance step, and until then confidence is a triage signal, not a quality guarantee.

**Phase 7 — Contract validation (deterministic, fail-closed).** Every record validates against the Source Data Dictionary JSON Schema contracts (to be written under `contracts/`, following the same pattern already proven in `knowledge/schemas/` + `validation.py`). Enforces the Charter §5.1 quality gates mechanically: 100% inventory coverage (every in-scope object/attribute has a record, `UNRESOLVED` included), no `INFERRED` value marked `OBSERVED`, no evidence-less inferred definition, every key/privacy classification/material relationship flagged for review. A validation failure returns the work item to Phases 3–6 with a bounded repair budget; it never persists as reviewable.

**Phase 8 — Human review checkpoint.** Validated `DRAFT` output, its `validation_finding`s, and its `open_question`s go to the durable review queue (`review_item`). To keep reviewer effort below the manual baseline (Charter §7) without weakening coverage, review is *targeted, not exhaustive*: Charter §5.1 requires every key, privacy classification, and material relationship to be reviewed, and every `INFERRED` definition — these are always queued, along with all `UNRESOLVED` items and critic-flagged contradictions. High-confidence `OBSERVED` physical facts (deterministic Phase 1 metadata that no inference depends on) are persisted and fully auditable but are *not* individually queued; they are available for spot-check and are surfaced in bulk rather than item-by-item. This preserves 100% inventory coverage (Phase 7) while spending human attention on inference and risk, not on restating catalog facts. The queuing threshold is itself a reviewable configuration, not a silent default. Reviewers approve, modify, reject, or defer at the object or attribute level; a material change triggers impact analysis before acceptance (Charter §5.4). Approved outcomes are written as `review_decision` records, which become durable input to the next run and to later Silver/Gold/STTM work — this is the only path to `APPROVED` status; nothing auto-approves.

**Phase 9 — Persistence and downstream generation.** Approved and still-draft records persist as versioned Delta tables, tagged with `artifact_version`, `run_id`, `context_snapshot_id`, and model/prompt/skill versions for reproducibility. The Excel workbook sheets (objects, attributes, relationships, code values, profiles — Charter §5.3 items 3–5) and the Databricks App's dictionary view are regenerated from these records; they are never edited independently and re-imported.

## 4. Output

The authoritative output is the set of Charter §5.2 "Evidence" and "Governance" family records this agent owns or contributes to:

`source_object_observation`, `source_attribute_observation`, `profile_evidence`, `relationship_candidate`, `evidence_item`, `open_question`, `validation_finding`, plus the `review_item` / `review_decision` records produced once a human acts on them.

Every record carries the Charter §5.1 field groups:

| Field group | Content |
|---|---|
| Scope and identity | engagement, source system, LOB, domain, schema, object, attribute, ordinal position |
| Physical definition | type, length, precision, scale, nullability, default, constraint, index, observed key role — all Phase 1, deterministic |
| Business definition | proposed name, definition, purpose, synonyms, subject area, lifecycle meaning — all Phase 3/4, LLM, evidence-cited |
| Values and profiling | approved code/value meanings, null/distinct stats, formats, ranges, patterns, profile snapshot reference |
| Relationships | key role, parent/child object, cardinality, evidence, validation status |
| Governance | privacy/sensitivity class (candidate until steward review), owner, steward, reviewer, approval state |
| Trust | `OBSERVED` / `INFERRED` / `DECIDED` / `UNRESOLVED`, evidence references (or governing `review_decision` for `DECIDED`), confidence components, assumptions, contradictions, open questions |
| Lineage and reproducibility | metadata/profile query reference, context snapshot, run ID, model/prompt/skill versions, artifact version, timestamps |

Before review the artifact is `DRAFT`. It becomes an `APPROVED` project deliverable only through Phase 8 human action — never automatically, per Architecture §5.

The Excel workbook and Databricks App dictionary view are downstream **review/consumption formats**, regenerated from the Delta records above. They are not a second authority.

## 5. Guardrails specific to this agent

- Read-only tool access to metadata and profiling sources, scoped to the allow-listed `source_tables` for this run; no write access outside its own artifact/finding tables.
- Read access to the governed knowledge pack only through the fail-closed selector — never directory scanning, never a superseded or unapproved version.
- Untrusted document content (existing dictionaries, report definitions) is scanned for instruction-like content and treated as data, never as instructions.
- Cannot mark a value `OBSERVED` without a deterministic Phase 1 evidence item behind it.
- Cannot leave an object or attribute uncovered — `UNRESOLVED` is a valid terminal state, silence is not.
- Cannot finalize a privacy classification, an approval, or a governed-knowledge change.
- Time/cost/token/tool-call/recursion limits enforced by the harness, per Architecture §6.

## 6. Skills used

Per Architecture §7's criteria (recurring, bounded, clear I/O, benefits from explicit judgment, independently evaluable), this agent is a natural home for skills such as: analyzing a source subject area from mixed evidence, proposing candidate code-value meanings from profile distributions, and preparing a dictionary slice for architect review. LOB facts and source metadata stay in governed context and evidence stores — a skill only explains how to use them, per the same section.

## 7. Open dependencies

1. **Contracts don't exist yet.** This design implies `contracts/source_object_observation.schema.json`, `contracts/source_attribute_observation.schema.json`, `contracts/relationship_candidate.schema.json`, `contracts/evidence_item.schema.json`, `contracts/open_question.schema.json` — none are written. Nothing here is authoritative until they are, and Phase 7 cannot exist without them.
2. **An exact knowledge pack is now runtime-eligible, but the agent positive path is not yet executable.** Phase 0 resolves context through `select_approved_pack`, which now admits `public_us_pnc_personal_auto@0.6.0`. The remaining fail-closed gate is the `D23-08` engagement authorization, applicability and effective-date policy, followed by implementation of the context and semantic phases. The structural `evidence_state` vocabulary remains contract-owned; domain code sets and pack-owned handling vocabulary must use this exact pinned pack and the minimum applicable subset.
3. **No metadata/profiling tool integration exists yet.** Phase 1 assumes an allow-listed read tool against Unity Catalog and a profile store; neither is built. Profiling is load-bearing: Phase 2 cardinality signals and Phase 4 code-value inference both depend on it, so until it exists the agent degrades to metadata-only, which materially weakens exactly the inferences the charter values most. That degradation should be an explicit, recorded run mode, not a silent quality drop.
4. **No unseen proof-slice source exists yet** — this design is untested against real data, per the still-open blocker from the knowledge-pack work.
5. **Review queue and App views are still a shell** — `src/apps/model_review/app.py` is intentionally unbuilt pending these contracts, per its own placeholder text.

The natural next increment is still writing the JSON Schema contracts in item 1 — they have no external dependency and everything downstream needs them — but they should pin the decisions this design now commits to (the four-value `OBSERVED`/`INFERRED`/`DECIDED`/`UNRESOLVED` trust vocabulary and confidence-as-components) so the contracts don't churn immediately. Contracts and a first `runtime_eligible` pack slice (item 2) are the two things blocking any real exercise of this agent.
