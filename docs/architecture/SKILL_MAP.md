# Solution Skill Map

**Status:** Draft skill inventory (elaborates `AGENT_SOLUTION_ARCHITECTURE.md` §7 "Judicious use of `SKILL.md`")
**Governing documents:** `AGENT_SOLUTION_ARCHITECTURE.md` §2 (capabilities), §5 (guardrails), §6 (harness), §7 (skill criteria and declaration fields); `SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md` §9.1 (Source Dictionary skill activation); `TARGET_MODEL_AND_STTM_DATABRICKS_FLOW_DESIGN.md` §8.1 (Silver/Gold/STTM skill activation); `REQUIREMENTS_CHARTER.md` §8 question 5 (skill vs tool vs validator vs context), §7 (semantic quality on unseen labelled cases)
**Anti-drift gate:** This map does not create a deliverable; it decides *where the solution genuinely needs a skill* so that reasoning judgment is reusable and independently evaluable, and — equally — records what must **not** become a skill, to prevent the agent sprawl Architecture §7 warns against. No `SKILL.md` is authoritative until it is written under `skills/<name>/` and passes its own evaluation examples.

This is a design for review, not approved skills. It identifies candidates and how each is used; it does not scaffold the files.

## 1. When a work item becomes a skill (and when it does not)

A skill is a **reusable procedural playbook for a bounded reasoning task** — not a persona, a prompt dump, a fact store, or a substitute for code (Architecture §7). Apply Charter §8 question 5 to every work item and classify it into exactly one home:

| If the work item is… | Its home is… | Not a skill because… |
|---|---|---|
| Authorization, scope validation, identifiers, idempotency, persistence, approval-state, limits | **Deterministic code / harness** | Safety and invariants must not depend on model judgment |
| Metadata extraction, profiling math, type compatibility, exact source facts | **Tool** | Deterministic computation, not judgment |
| Contract, referential, grain, coverage, lineage, policy checks | **Validator** | A pass/fail rule, not a playbook |
| Glossary, code sets, LOB/domain facts, standards, approved reference models | **Governed context** | Content, not procedure; belongs in the knowledge layer, never inside a `SKILL.md` |
| A **recurring, bounded reasoning task** with clear I/O that benefits from explicit modeling judgment and can be evaluated independently | **Skill** | Meets all five §7 gates |

A candidate is a skill **only when all five §7 gates hold**: (1) it recurs across engagements or model elements; (2) it has a stable objective and bounded responsibility; (3) its inputs and output contract are clear; (4) it carries domain/modeling judgment that benefits from explicit guidance; (5) it can be evaluated independently. If any gate fails, push the work into code, a tool, a validator, or governed context instead.

Every skill in §3 must eventually declare the full §7 field set: trigger / non-trigger, purpose and scope, required inputs and permitted evidence, applicable tools and prohibitions, stepwise method and reasoning checkpoints, output contract, mandatory validations, escalation and stop conditions, evaluation examples, and version + owner. This map fixes all of those except the stepwise method (which belongs in the `SKILL.md` itself).

## 2. How skills are used

Runtime modeling skills are not always-on. Per Architecture §4.1 and §6, the harness's **applicable-skill resolver** selects the skill versions relevant to the current task and includes them in the bounded context envelope alongside tool permissions and limits. A skill only *explains how to retrieve and apply* governed context and evidence — the LOB facts, source metadata, and engagement decisions themselves stay in the governed stores and arrive as evidence, never baked into the skill (Architecture §7).

Authoring-plane skills run outside the engagement modeling harness. Knowledge maintainers may create governed candidates; contract and solution-build skills may create specifications, deterministic code, tests and build evidence. None may approve artifacts, publish knowledge for runtime, execute an engagement, or write engagement/source facts into reusable public knowledge.

Each skill run is traced in MLflow with its skill version captured for reproducibility (Charter §5.2 run evidence; §7 reproducibility). A skill's output is still a `DRAFT` proposal: it passes through the same contract validation, critic pass, and human-review gates as any other agent output (Architecture §5). No skill output is a deliverable on its own.

## 3. Skill inventory

Fourteen skills total: three runtime cross-cutting skills, eight aligned to the five reasoning-capable producer/critic capabilities, and three authoring-plane skills. The Scope & Context Manager intentionally has no runtime skill. Runtime candidates remain design inventory; owner direction prioritizes solution-building authoring skills before runtime Skill implementation or a future solution-runner Skill.

### 3.1 Cross-cutting (shared by every producing capability)

**X1 — prepare-artifact-for-review**
- *Trigger:* a validated `DRAFT` artifact slice is ready to enter the review queue. *Non-trigger:* the artifact still has contract-validation failures, or no human review is required for the slice.
- *Inputs / permitted evidence:* the artifact records, their `validation_finding`s, `open_question`s, confidence components, and evidence citations.
- *Tools / prohibitions:* read-only over the artifact and finding stores; artifact-write only to the `review_item` store. May not alter the artifact's semantic content or approve anything.
- *Output contract:* a `review_item` bundle — reviewer-facing summary, the material decisions to confirm, unresolved items, and evidence drill-through references (Charter §5.4 App contract).
- *Mandatory validations:* every material element carries an evidence or decision citation; nothing marked `APPROVED`; targeted-review gating applied (keys, privacy, material relationships, `INFERRED`, `UNRESOLVED`, contradictions surfaced; high-confidence `OBSERVED` facts summarized in bulk).
- *Escalation / stop:* stop and raise if any queued item lacks a citation or if targeting rules are ambiguous.
- *Evaluation:* reviewer-effort and completeness on unseen review bundles vs a manual-prep baseline.
- *Depends on:* review-item contract; App review view.

**X2 — formulate-clarification-question**
- *Trigger:* a gap, contradiction, or insufficient-evidence condition is detected and no prior human decision resolves it. *Non-trigger:* evidence is sufficient, or a `review_decision` already answers it.
- *Inputs / permitted evidence:* the conflicting/insufficient evidence set, the governed concept it touches, prior decisions.
- *Tools / prohibitions:* read-only over evidence and decisions. May not invent a resolution or default the answer.
- *Output contract:* an `open_question` record — the precise question, what evidence would resolve it, the blocked element(s), and severity.
- *Mandatory validations:* question is answerable and scoped; links to the specific element(s) it blocks; no leading/assumed answer.
- *Escalation / stop:* stop if the same question recurs unresolved across runs (flag as a standing blocker).
- *Evaluation:* question usefulness and resolution rate judged by SMEs on unseen gaps.
- *Depends on:* open_question contract.

**X3 — assess-change-impact**
- *Trigger:* a reviewer proposes a material modification, or an upstream approved decision changes (Charter §5.4 impact analysis before acceptance). *Non-trigger:* cosmetic or non-material edits.
- *Inputs / permitted evidence:* the proposed change, `artifact_dependency` / `lineage_edge` records, downstream Silver/Gold/STTM artifacts.
- *Tools / prohibitions:* read-only over dependency and lineage stores; write only impact findings. May not apply the change or approve it.
- *Output contract:* an impact report — affected downstream elements, coverage/lineage consequences, and re-validation or regeneration needed.
- *Mandatory validations:* dependency traversal is complete for the changed element; every claimed impact cites a dependency/lineage edge.
- *Escalation / stop:* stop if lineage is incomplete for the changed element (cannot assert "no impact" without evidence).
- *Evaluation:* precision/recall of predicted impacts against SME-labelled change cases.
- *Depends on:* artifact_dependency and lineage_edge contracts.

### 3.2 Source Data Analyst (SDD Agent) — see `SOURCE_DATA_DICTIONARY_AGENT_DESIGN.md` and `SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md`

**SA1 — analyze-source-subject-area** (Architecture §7 candidate; SDD design Phases 3–4)
- *Trigger:* an in-scope object/attribute slice has its Phase 1–2 evidence bundle assembled. *Non-trigger:* evidence not yet ingested, or the slice is out of the allow-listed source boundary.
- *Inputs / permitted evidence:* `source_object_observation`, `source_attribute_observation`, `profile_evidence`, `relationship_candidate`, scoped glossary/domain knowledge, prior `review_decision`s.
- *Tools / prohibitions:* read-only over evidence and the approved pack via the fail-closed selector. May not invent fields, meanings, or evidence references; may not finalize privacy or approval.
- *Output contract:* candidate business name, definition, purpose, subject area, synonyms, lifecycle meaning — each tagged `OBSERVED` / `INFERRED` / `DECIDED` / `UNRESOLVED`, with citations for anything not `OBSERVED`.
- *Mandatory validations:* no `INFERRED` claim without a cited `evidence_item`; insufficient evidence yields `UNRESOLVED` + `open_question`; no meaning substitutes for structural evidence.
- *Escalation / stop:* emit `UNRESOLVED` rather than guess; route cross-object contradictions to the critic (CR1).
- *Evaluation:* definition/name accuracy on unseen, independently labelled attributes (Charter §7) — no evaluation answers in the skill.
- *Depends on:* SDD evidence contracts; runtime-eligible governed pack.

**SA2 — propose-code-value-meanings** (SDD design §6; Phase 4 coded attributes)
- *Trigger:* an attribute is enumerated/coded and has a profile value distribution. *Non-trigger:* free-text or continuous attributes; no profile available.
- *Inputs / permitted evidence:* profile value distribution, contract-owned `evidence_state`, governed code sets (`unknown_handling_state` and domain code sets), any existing-document value hints.
- *Tools / prohibitions:* read-only over profiles and approved code sets. May not invent a code value or collapse unknown/missing/invalid/withheld/unmapped into one another.
- *Output contract:* candidate value-to-meaning proposals cross-referenced to governed code sets; unmapped values flagged via `unknown_handling_state` (`UNMAPPED`), never invented.
- *Mandatory validations:* every proposed mapping cites a governed code and a profile frequency; residual values explicitly stated as `UNMAPPED`.
- *Escalation / stop:* stop and raise an `open_question` when the distribution conflicts with the governed code set.
- *Evaluation:* mapping accuracy and unmapped-recall on unseen coded attributes.
- *Depends on:* code_set contracts; profiling tool.

**SA3 — classify-attribute-sensitivity** (SDD design Phase 4 privacy)
- *Trigger:* an attribute matches a privacy-relevant pattern (name/address/DOB/government-ID etc.). *Non-trigger:* no sensitivity signal, or a privacy class is already `DECIDED` by a steward.
- *Inputs / permitted evidence:* attribute name/type/profile patterns, governed privacy guidance.
- *Tools / prohibitions:* read-only. **Always routes to `privacy_steward`; may never finalize a privacy class.**
- *Output contract:* a *candidate* sensitivity classification citing governed privacy guidance, marked pending steward review.
- *Mandatory validations:* candidate cites governed guidance; steward-review routing is attached; class remains non-final.
- *Escalation / stop:* any ambiguous or high-risk match escalates to the steward with the evidence.
- *Evaluation:* precision/recall against SME-labelled sensitive attributes; false-negative cost weighted high.
- *Depends on:* governed privacy guidance in the pack; steward review path.

### 3.3 Silver ODS Modeler — see `TARGET_MODEL_AND_STTM_DATABRICKS_FLOW_DESIGN.md`

**SL1 — design-silver-entity-and-history** (Architecture §7 candidate)
- *Trigger:* an approved SDD slice is available for source-aligned modeling. *Non-trigger:* the SDD slice is not yet approved for the elements in question.
- *Inputs / permitted evidence:* approved SDD records, keys/relationships, governed modeling standards, prior decisions.
- *Tools / prohibitions:* read-only over approved artifacts and standards; writes only Silver draft records. May not deploy schemas or invent source coverage.
- *Output contract:* `silver_entity` / `silver_attribute` / `silver_relationship` / `silver_history_rule` proposals with entity boundaries, history strategy, standardization, and source-coverage citations.
- *Mandatory validations:* every element traces to an approved SDD element or decision; history/grain internally consistent; standardization cites a governed standard.
- *Escalation / stop:* raise an `open_question` where source evidence underdetermines the boundary or history choice.
- *Evaluation:* architect-approved checks on grain/keys/history/naming (Charter §7 model quality) on unseen slices.
- *Depends on:* Silver contracts; approved SDD output.

*(Standardization and source-aligned data-quality rule design are folded into SL1 for now; split into a separate skill only if they recur independently of entity design.)*

### 3.4 Gold Dimensional Modeler — see `TARGET_MODEL_AND_STTM_DATABRICKS_FLOW_DESIGN.md`

**GD1 — determine-fact-grain** (Architecture §7 candidate)
- *Trigger:* a requirement or measure set needs a fact table designed. *Non-trigger:* no supporting Silver elements exist yet.
- *Inputs / permitted evidence:* analytical/reporting requirements, approved Silver elements, governed standards.
- *Tools / prohibitions:* read-only; writes Gold draft records. May not invent measures or requirements.
- *Output contract:* `gold_fact` grain statement, candidate measures, and the Silver elements that support them, with requirement citations.
- *Mandatory validations:* grain is a single explicit statement; every measure traces to a requirement and to supporting Silver elements; additivity stated.
- *Escalation / stop:* raise an `open_question` when requirements imply conflicting grains.
- *Evaluation:* grain/measure correctness on unseen requirement sets vs SME baseline.
- *Depends on:* Gold contracts; approved Silver; requirement records.

**GD2 — design-conformed-dimension** (Architecture §7 candidate)
- *Trigger:* a dimension is shared across facts or requirements. *Non-trigger:* a single-fact private dimension with no conformance need.
- *Inputs / permitted evidence:* requirements, approved Silver entities, existing conformed dimensions, governed standards.
- *Tools / prohibitions:* read-only; writes Gold draft records. May not silently diverge from an existing conformed dimension.
- *Output contract:* `gold_dimension` with attributes, SCD behavior, and conformance mapping across facts.
- *Mandatory validations:* conformance is explicit; SCD behavior justified by evidence; reuse of existing conformed dimensions preferred over new ones.
- *Escalation / stop:* raise a contradiction when two facts require incompatible dimension definitions.
- *Evaluation:* conformance correctness and SCD-appropriateness on unseen dimensions.
- *Depends on:* Gold contracts; conformance rules.

### 3.5 STTM & Lineage Modeler — see `TARGET_MODEL_AND_STTM_DATABRICKS_FLOW_DESIGN.md`

**ST1 — create-and-validate-sttm-slice** (Architecture §7 candidate)
- *Trigger:* a source→Silver or Silver→Gold mapping slice is needed for approved model elements. *Non-trigger:* the target elements are not yet approved.
- *Inputs / permitted evidence:* approved source/Silver/Gold elements, transformation requirements, governed rules.
- *Tools / prohibitions:* read-only over approved artifacts; writes mapping draft records. May not invent source fields or leave a required target attribute silently unmapped.
- *Output contract:* `attribute_mapping` / `transformation_rule` / `lookup_rule` / `reconciliation_rule` with source, derivation, defaults, exceptions, DQ rules, lineage, and reconciliation criteria.
- *Mandatory validations:* every required target attribute has a source, a derivation, a default, or a documented gap (Charter §7 mapping completeness); lineage edges recorded.
- *Escalation / stop:* raise an `open_question` for any target attribute without a defensible source or gap.
- *Evaluation:* mapping completeness and transformation correctness on unseen target sets.
- *Depends on:* Mapping/lineage contracts; approved source and target models.

### 3.6 Model Critic & Validator

**CR1 — coverage-and-consistency-critique** (Architecture §7 candidate; SDD design Phase 5 critic)
- *Trigger:* any producer emits a validated `DRAFT` slice. *Non-trigger:* the slice failed deterministic contract validation (fix that first).
- *Inputs / permitted evidence:* the draft artifact, its evidence, requirements, prior decisions, and the governed glossary/standards.
- *Tools / prohibitions:* read-only; writes only `validation_finding` / `open_question`. **Must run under a different model and/or reduced context than the producer where the approved model list allows** — rephrasing a rubric alone does not make the critic independent, and agreement is treated as correlated, not independent, confirmation.
- *Output contract:* challenges to grain, keys, history, coverage, evidence sufficiency, contradictions, and mapping completeness, each as a finding with severity.
- *Mandatory validations:* every finding cites the element and the evidence it challenges; coverage gaps enumerated against the inventory/requirements.
- *Escalation / stop:* unresolved challenges become `open_question`s, never silent defaults.
- *Evaluation:* defect-detection rate and false-alarm rate on unseen slices with seeded errors.
- *Depends on:* all producer contracts; harness model router with ≥2 approved models.

### 3.7 Scope & Context Manager

No dedicated skill at this time. Scope validation, context-envelope assembly, filtering, and fail-closed selection are deterministic (Architecture §4.1, §5) — they are code, tools, and validators, not judgment playbooks. The one judgment-bearing activity nearby — reconciling conflicting or stale context — is handled by CR1 (critique) and X2 (clarification), so a separate context skill would duplicate them. Revisit only if context reconciliation develops a recurring, independently evaluable judgment pattern of its own.

### 3.8 Knowledge Pack Maintainer — authoring plane, outside runtime harness

**KM1 — build-governed-knowledge-pack** (`skills/build-governed-knowledge-pack/SKILL.md`)
- *Trigger:* create a candidate knowledge pack for a new LOB/jurisdiction, add a governed jurisdiction extension, create a new immutable version after approved source changes, or validate/repair a candidate. *Non-trigger:* engagement evidence, Source Dictionary/Silver/Gold/STTM generation, ontology creation, pack approval, or runtime promotion.
- *Inputs / permitted evidence:* explicit pack plan, canonical schemas, approved source-use policy, authoritative/public/licensed sources as permitted, prior immutable manifest lineage, completeness rubric, named owners/reviewers.
- *Tools / prohibitions:* may research, scaffold a new candidate version, write only the new candidate/source registry, run deterministic validators and compute fingerprints. May not overwrite an immutable version, import client evidence into a public pack, reproduce unauthorized content, assign `APPROVED`, or set runtime eligibility.
- *Output contract:* immutable `CANDIDATE` pack with manifest, source registry, claim-level provenance, modules/assets, completeness/gaps, validation result and reviewer queue.
- *Mandatory validations:* schema/path/fingerprint/source-ID integrity, claim-level citations for material new claims, weights and score arithmetic, layer/jurisdiction separation, usage-rights state, no silent ontology, candidate/non-runtime lifecycle.
- *Escalation / stop:* stop on unsupported claims, conflicting/expired authority, unknown applicability/effective date, missing content rights, missing owner/reviewer, or any request to auto-approve.
- *Evaluation:* forward-test on an unseen different LOB and a different jurisdiction; measure unsupported-claim rate, citation coverage, jurisdiction leakage, completeness calibration and reviewer corrections.
- *Depends on:* knowledge schemas/validator, canonical structure, source-use policy and named SME/regulatory/content-rights review.

### 3.9 Contract Maintainer — authoring plane, outside runtime harness

**KM2 — author-source-discovery-contracts** (`skills/author-source-discovery-contracts/SKILL.md`)
- *Trigger:* author or revise the Increment-1 control, snapshot, evidence, requirement, dictionary, governance, lineage, handoff or skill-resolution contracts. *Non-trigger:* runtime semantic analysis, profiling, approval, knowledge promotion, or Silver/Gold/STTM contracts.
- *Inputs / permitted evidence:* intact governing requirements/designs, machine-readable contract inventory, common structural schema, approved architecture decisions and Increment 2–3 interface requirements.
- *Tools / prohibitions:* may author contract specifications, neutral scaffolds, validation behavior and synthetic evaluations. Genie Code builds production schemas/tools. May not edit governing documents, embed business answers, approve artifacts, or change pack runtime eligibility.
- *Output contract:* complete draft contract inventory and versioned schema/validator/test specifications with structural and referential gates.
- *Mandatory validations:* inventory count/reference/order, schema/version/common-ref integrity, vocabulary ownership, typed-claim behavior, evidence scope, lifecycle guards and multi-family forward tests.
- *Escalation / stop:* stop on damaged governing documents, missing field ownership, Increment 1–3 interface conflict or unresolved human governance decision.
- *Evaluation:* unseen synthetic records across append-only, operational, governance-decision, open-item, material and handoff lifecycle families.
- *Depends on:* controlling architecture, Requirements Charter, Source Dictionary designs and the accepted contract-ownership ADR.

### 3.10 Source Discovery Foundation Builder — authoring plane, outside runtime harness

**B2 — build-source-discovery-foundation** (`skills/build-source-discovery-foundation/SKILL.md`)
- *Trigger:* implement or revise deterministic `I23-00..08` components that move an authorized work package from `VALIDATED` through `EVIDENCE_READY` to `CONTEXT_READY`. *Non-trigger:* semantic SDD generation, solution execution, contract invention, knowledge approval, or downstream Silver/Gold/STTM work.
- *Inputs / permitted evidence:* approved Increment-1 contracts, Increment-2/3 implementation specifications, build handoff, accepted decisions, repository package/DAB conventions and authorized synthetic fixtures.
- *Tools / prohibitions:* may build DAB/Lakeflow resources, control/source-adapter/evidence/context/persistence modules, thin workflows, tests and build evidence. May not modify governing documents or decisions, approve/promote knowledge, access unauthorized live data, or perform semantic reasoning.
- *Output contract:* dedicated source-discovery job, deterministic Phase A/Phase B modules and tests, plus one machine-validated builder handoff covering every `I23-00..08` work package.
- *Mandatory validations:* contract/task ownership, bundle/job-parameter validation, read/write isolation, completeness, privacy leakage, provenance separation, exact knowledge selection, idempotency, fingerprint/invalidation and readiness gates.
- *Escalation / stop:* stop on missing/ambiguous contracts, open live-positive-path decisions, unauthorized source/policy, unreconciled coverage, ambiguous knowledge selection or any requested governance mutation.
- *Evaluation:* positive and fail-closed cases in the packaged evaluation matrix; verified work packages require cited contracts, files and tests; full completion also requires authorized proof-slice thresholds and architecture review.
- *Depends on:* approved Increment-1 contracts and accepted decisions for each live/positive path. Negative and isolated synthetic development may proceed without weakening those gates.

## 4. Deliberately not skills (anti-sprawl register)

Kept in code / tools / validators / governed context on purpose:

- scope validation, identifiers, idempotency, persistence, versioning, approval-state enforcement, cost/loop limits — **harness code**;
- metadata extraction, profiling mathematics, type compatibility, exact source facts — **tools**;
- relationship-candidate *detection* heuristics and support scoring (SDD Phase 2), and confidence scoring (SDD Phase 6) — **deterministic code** (the *business meaning* of a relationship is skill work in SA1; the detection is not);
- contract, referential, grain, coverage, lineage, and policy checks (SDD Phase 7 and equivalents) — **validators**;
- glossary, code sets, KPI definitions, LOB/domain facts, modeling standards, approved reference models — **governed context**, never inside a `SKILL.md` (Architecture §7). A skill may explain how to retrieve and apply them, but must not contain them.
- the knowledge itself remains governed context; only its repeatable candidate-authoring, provenance, validation and review-preparation procedure belongs in **KM1**.
- contract schemas and validators remain deterministic artifacts; only their repeatable governed authoring and evaluation procedure belongs in **KM2**.
- Increment-2 and Increment-3 code remains deterministic; only the repeatable builder procedure and evidence handoff belongs in **B2**. The overlapping `author-source-onboarding` and `author-context-assembly` drafts are retired rather than kept as competing authorities.

## 5. Readiness and sequencing

Every runtime modeling skill above depends on two things this project has not built yet (see `SOURCE_DATA_DICTIONARY_AGENT_DESIGN.md` §7): the JSON Schema contracts each skill's output must validate against, and at least one `runtime_eligible` governed pack for the skills that read governed context. Runtime Skills should not be authored ahead of their output contracts, or they will churn.

KM1 is an exception to the runtime sequencing paragraph above because it helps create governed pack candidates; it depends on knowledge-pack schemas and deterministic validation rather than on a runtime-eligible pack. It still cannot promote its own output.

KM2 is also authoring-plane only. The controlling architecture is restored, so KM2 may now be used to author the Increment-1 contract suite. Contract publication remains `DRAFT` until the generated schemas, validators and evaluations are reviewed through the normal architecture and human-governance gates.

B2 is the current solution-build priority. It may validate contract alignment now, but producer implementation stops at the Increment-1 contract gate. After approved contracts exist, it may build all negative and isolated synthetic paths; live source and project-knowledge positive paths remain gated by the applicable `D23-*` decisions.

Deferred runtime-Skill build order, following the producing order of the deliverables:

1. **X1, X2** (prepare-for-review, clarification) — small, cross-cutting, and exercisable as soon as any artifact and the review contracts exist.
2. **SA1, SA2, SA3** — the Source Data Analyst skills; first producer the project needs, and the richest judgment surface.
3. **CR1** — the critic; needed to close the SDD Phase 5 loop and reusable by every later producer.
4. **SL1 → GD1, GD2 → ST1 → X3** — as Silver, Gold, STTM, and change-impact come online.

The authoring-plane **KM1** may be used now to create new candidate packs, but it must pass its unseen LOB/jurisdiction evaluation before being treated as production-grade authoring automation.

Author each `SKILL.md` only after its output contract is written, and gate it on its own evaluation examples (Charter §7: measured on unseen, independently labelled cases; no evaluation-set answers inside the skill).

The phase-level resolver mappings are split at the approved Source Data Dictionary boundary: [`SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md`](source-data-dictionary/SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md) §9.1 governs source discovery/dictionary skills, and [`TARGET_MODEL_AND_STTM_DATABRICKS_FLOW_DESIGN.md`](target-modeling/TARGET_MODEL_AND_STTM_DATABRICKS_FLOW_DESIGN.md) §8.1 governs Silver/Gold/STTM skills. This inventory defines each candidate's trigger; the runtime resolver must enforce it and may not treat a `DRAFT` upstream artifact as `APPROVED`.
