# Agentic Data Analyst and Modeler — Agent Solution Architecture

**Status:** Controlling solution architecture  
**Effective date:** 2026-07-15  
**Governing requirements:** [`REQUIREMENTS_CHARTER.md`](../requirements/REQUIREMENTS_CHARTER.md)  
**Change control:** Architecture may evolve without changing product requirements. If an architecture decision conflicts with the Requirements Charter, the Requirements Charter takes precedence.

This document defines how the required Source Data Dictionary, Silver ODS model, Gold dimensional model, STTM, coverage, and review capabilities are implemented. It does not redefine product scope or deliverables.

**Related detailed designs:**

- [`SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md`](source-data-dictionary/SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md) — source registration, metadata, controlled profiling, evidence/context assembly, Source Data Dictionary reconstruction, approval, and handoff.
- [`TARGET_MODEL_AND_STTM_DATABRICKS_FLOW_DESIGN.md`](target-modeling/TARGET_MODEL_AND_STTM_DATABRICKS_FLOW_DESIGN.md) — downstream Silver ODS, Gold dimensional model, requirement coverage, STTM, lineage, review, and publication flow consuming an approved dictionary handoff.
- [`SOURCE_DATA_DICTIONARY_AGENT_DESIGN.md`](source-data-dictionary/SOURCE_DATA_DICTIONARY_AGENT_DESIGN.md) — Source Data Analyst component design and reconstructed dictionary phases.
- [`SKILL_MAP.md`](SKILL_MAP.md) — candidate procedural skill inventory, runtime triggers, non-triggers, dependencies, evaluation boundaries, and anti-sprawl decisions.

## 1. LLM-first, evidence-grounded implementation principle

Use LLMs and agents wherever the task requires semantic interpretation, synthesis, alternative evaluation, or modeling judgment. Do not hard-code expected answers merely to make a demonstration appear deterministic.

### LLM/agent responsibilities

- infer candidate business meaning from multiple evidence types;
- identify domains, LOB semantics, entities, relationships, and business rules;
- propose and critique Silver entity boundaries and normalization choices;
- determine candidate Gold grain, facts, dimensions, and measures from requirements;
- draft transformation logic and STTMs;
- detect semantic conflicts and generate targeted clarification questions;
- explain decisions with evidence citations; and
- revise artifacts after reviewer feedback.

### Code and deterministic control responsibilities

- authorization, evidence classification, and tool permissions;
- metadata extraction, profiling mathematics, type compatibility, and exact source facts;
- workflow state, identifiers, idempotency, retries, dependency tracking, and versioning;
- schema and contract validation;
- referential, grain, lineage, completeness, and policy validation;
- cost, token, time, and loop limits; and
- persistence, audit, and approval-state enforcement.

Deterministic rules are appropriate for true invariants, approved standards, and safety controls. A lookup that encodes the desired semantic answer for test fields is not an acceptable substitute for agent reasoning. All semantic quality claims require evaluation on unseen, independently labelled cases.

## 2. Agent solution

The initial implementation uses **one custom agent harness with specialist capabilities**, not many independently deployed agents by default. A capability becomes a separate deployed agent only when it needs a materially different context boundary, tool authority, lifecycle, scaling profile, or evaluation regime.

| Capability | Responsibility | Primary output |
|---|---|---|
| Scope and context manager | Fix solution run, LOB, domain, source boundary, requirements, governed inputs, and context snapshot | Executable bounded context |
| Source Data Analyst | Reconstruct source meaning, structure, relationships, code values, evidence, and gaps | Reconstructed Source Data Dictionary |
| Silver ODS Modeler | Create scalable source-aligned/canonical ODS design | Silver model |
| Gold Dimensional Modeler | Create requirement-driven facts, dimensions, grain, and measures | Gold model |
| STTM and Lineage Modeler | Map source to Silver and Silver to Gold with transformation and lineage | STTM package |
| Model Critic and Validator | Challenge grain, keys, history, coverage, evidence, contradictions, and mapping completeness | Validation findings |
| Review coordinator | Route material decisions, record feedback, and trigger targeted revision | Decisions and approved artifacts |

Specialist capabilities must work through explicit input/output contracts. They may debate or critique one another, but no conversational output is a deliverable until it passes contract and policy validation.

## 3. Databricks technology choices

The product choices shown in the Databricks “Create new Agent” screen are complementary:

| Databricks capability | Applicable use in this solution | Decision |
|---|---|---|
| **Code your own agent / Custom Agent** | Stateful modeling workflow, specialist reasoning, custom tools, structured artifacts, checkpoints, human review, and long-running work | **Core implementation** |
| **Supervisor Agent** | Later conversational entry point that routes user requests to the modeling agent, Genie, and approved tools | Optional outer experience after the core harness is proven |
| **Information Extraction / `ai_extract`** | Extract structured requirements, definitions, mappings, and rules from approved documents with citations | Bounded evidence-extraction tool, not the modeler |
| **Text Classification / `ai_classify`** | Candidate LOB/domain/document classification and work routing | Bounded helper with evaluation and override |
| **Genie Space** | Ask questions of approved source-analysis, model, STTM, and coverage tables | Consumption and exploration only; not an authoring authority |
| **Databricks Apps (Streamlit initially)** | Model/STTM review, comparison, decisions, gaps, evidence, and exports | Primary human review interface |
| **MLflow for GenAI** | Trace, evaluate, compare, monitor, and collect expert feedback | Mandatory harness component |
| **Unity Catalog and Delta** | Govern evidence and persist versioned artifacts and decisions | Authoritative data/control plane |
| **Databricks Labs DQX** | Programmatic source profiling and later execution of approved data-quality rules behind a versioned adapter | Profiling engine; solution-owned scope, privacy, persistence and approval controls remain authoritative |
| **AI Search** | Retrieve only approved unstructured evidence with run, source, and LOB/domain filters | Optional evidence service; never unfiltered memory |

The custom agent should follow the Databricks-recommended MLflow `ResponsesAgent` interface so the implementation can use custom orchestration while retaining tracing, evaluation, deployment, and monitoring integration. Product previews or beta services must sit behind an adapter and cannot become an irreplaceable core dependency.

Current platform references:

- [Build AI agents on Databricks](https://docs.databricks.com/aws/en/agents)
- [Author a custom agent on Databricks Apps](https://docs.databricks.com/aws/en/agents/agent-framework/author-agent)
- [Build a multi-agent system on Databricks Apps](https://docs.databricks.com/aws/en/agents/agent-framework/multi-agent-apps)
- [`ai_extract` with schemas, citations, and confidence](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract)
- [MLflow tracing](https://docs.databricks.com/aws/en/mlflow3/genai/tracing)
- [Databricks Apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps)

## 4. Context engineering contract

Context is an engineered, versioned input—not a prompt containing everything available.

### 4.1 Governed knowledge layer

The knowledge layer supplies authorized context to the agent harness. It is separate from source evidence, prompts, skills, working memory, and generated artifacts.

It has four planes:

1. **Portable pack source:** versioned manifests and non-sensitive pack assets under `knowledge/`.
2. **Governed registry:** Unity Catalog/Delta records for pack identity, version, scope, ownership, approval, effective dates, authorization, and fingerprints.
3. **Governed content:** structured Delta records and, where approved, documents in Unity Catalog Volumes or filtered AI Search indexes.
4. **Runtime context:** the context assembler selects the smallest applicable subset for one solution run, LOB/domain, product/module/version, effective date, task, and approval state.

Knowledge categories include supplied ontology, business glossary, modeling standards, LOB knowledge, domain knowledge, KPI definitions, code sets, and authorized target reference models.

Agents have read/retrieval access to eligible knowledge and write generated results only to solution-owned artifact and review stores. They cannot publish, modify, approve, or silently extend governed knowledge packs. Missing, expired, unauthorized, ambiguous, or cross-version knowledge remains unavailable or unresolved.

Every task receives a bounded **context envelope** containing:

1. charter and applicable policies;
2. solution run, LOB, domain, source, and target scope;
3. task objective and output contract;
4. approved ontology/glossary/standards inputs, when supplied;
5. task-relevant source evidence and requirement evidence;
6. upstream artifacts and their approval/version status;
7. prior approved decisions and unresolved contradictions;
8. applicable skill versions;
9. tool permissions and limits; and
10. context snapshot ID and evidence citations.

The context assembler must:

- filter by memory partition, LOB, domain, source, artifact type, version, effective date, and approval state;
- prefer authoritative and approved evidence;
- distinguish source fact, governed input, inference, requirement, and human decision;
- retrieve the smallest sufficient context rather than dumping whole repositories;
- retain evidence IDs so every material output can cite its support;
- detect conflicting and stale context;
- set token budgets and summarize only with retained provenance;
- prevent one run's source facts from entering another run and prevent decisions from crossing memory partitions; and
- fail closed when essential evidence is missing or contradictory.

Chat history is not authoritative memory. Working memory is run-scoped; durable memory consists only of versioned evidence, artifacts, and approved decisions.

### 4.2 Memory taxonomy — episodic, semantic, procedural

The durable-memory principle above resolves into three named stores, mapped to the cognitive memory systems, plus deterministic execution which is not memory. Every persistent thing the solution keeps must classify into exactly one store. See [`ADR-004`](../decisions/ADR-004-memory-taxonomy.md).

| Store | Memory type | Holds | Scope | Lifecycle |
|---|---|---|---|---|
| Governed knowledge layer (§4.1) | **Semantic** | General domain meaning: glossary, code sets, LOB/domain modules, standards, approved reference models | Cross-run, reusable | Versioned pack; `CANDIDATE` → `APPROVED`; immutable versions |
| Decision and run stores | **Episodic** | Events bound to run/time: authorized schema-scope policy, resolved frozen source manifest, `review_decision`, `open_question`, `context_snapshot`, `solution_run`, `artifact_version` | Run-, source-, and memory-partition-isolated | Append-only / versioned; never auto-promoted |
| Skills (`SKILL.md`, §7) | **Procedural** | How to perform a bounded, evaluable reasoning task | Reusable playbook | Versioned; gated on unseen evaluation cases |

Deterministic scope/authorization gates (`00_validate_scope.py`, tool-permission middleware, approval-state enforcement) are execution, not memory.

Placement is then mechanical: a general truth about the domain is semantic; a fact or decision true only for one run or source boundary is episodic; a reusable procedure is procedural; a safety invariant is deterministic code. Domain content never enters a skill, and run-specific source data never enters the knowledge layer.

**Consolidation gate (episodic → semantic).** Repeated approved decisions may reveal a generalizable pattern worth adding to reusable knowledge (Charter §7 — reducing reviewer overrides through learning). That promotion is a governed, human-reviewed authoring act performed through the knowledge-pack maintainer plane ([`build-governed-knowledge-pack`](../../skills/build-governed-knowledge-pack/SKILL.md)); it strips run- and source-specific facts, cannot be an automatic or silent write, and may not set `APPROVED` or `runtime_eligible`. Memory isolation (Charter §6) bounds it: episodic decisions must never cross partitions except through approved semantic knowledge.

## 5. Guardrails

Guardrails are enforced in the harness and data plane, not merely written in prompts.

### Before an agent call

- validate scope and user/app identity;
- authorize every evidence class and retrieval source;
- exclude prohibited or cross-run content;
- scan untrusted documents for instruction-like content and treat it as data;
- assemble only applicable skills and tools; and
- require a versioned output contract.

### During an agent call

- constrain read-only source tools to the authorized catalog/schema and the resolved frozen source manifest, and writes to solution-owned artifact stores;
- separate source reads from artifact writes;
- constrain tool arguments to the solution-run and source scope;
- enforce time, cost, token, tool-call, and recursion limits;
- require structured intermediate and final outputs;
- prohibit invented source fields, concept IDs, requirements, and evidence references; and
- trace model calls, retrieval, tool calls, skills, and state transitions.

### After an agent call

- validate contracts and referential integrity;
- validate grain, keys, model coverage, STTM completeness, lineage, and citations;
- run a critic pass using an independently phrased rubric;
- route contradictions and material modeling choices for human review;
- persist only validated artifacts; and
- prohibit automatic `APPROVED` status.

No agent receives production deployment, migration execution, credential management, or unrestricted SQL authority.

## 6. Agent harness requirements

The harness is a product component, not notebook glue. It must provide:

- typed request, context, artifact, finding, decision, and run contracts;
- durable state machine/checkpoints for long-running work;
- context assembler and evidence citation service;
- model router with approved model list and task-specific settings;
- skill registry and applicable-skill resolver;
- scoped tool registry with policy middleware;
- structured-output validation and repair limits;
- retries, idempotency, dependency invalidation, and resumability;
- human decision checkpoints and targeted regeneration;
- MLflow tracing, evaluation, prompt/model/skill version capture, cost, and latency;
- offline golden sets, adversarial tests, unseen cases, and regression gates;
- online monitoring for quality, policy violations, cost, latency, and reviewer overrides; and
- a Databricks App for review rather than relying on chat alone.

## 7. Judicious use of `SKILL.md`

A skill is a reusable procedural playbook, not an agent persona, fact store, prompt dump, or substitute for code.

Create a skill only when all are true:

- the activity recurs across solution runs or model elements;
- it has a stable objective and bounded responsibility;
- its required inputs and output contract are clear;
- it contains domain/modeling judgment that benefits from explicit guidance; and
- it can be evaluated independently.

Good candidates include:

- analyze a source subject area;
- design a Silver entity and history strategy;
- determine a fact table's grain;
- design a conformed dimension;
- create and validate an STTM slice;
- perform model and requirement coverage critique; and
- prepare an artifact for architect review.

LOB facts, ontology content, source metadata, and run-specific decisions belong in governed context stores, not inside `SKILL.md`. A skill may explain how to retrieve and apply them.

Knowledge-pack authoring is a separate maintainer plane. [`build-governed-knowledge-pack`](../../skills/build-governed-knowledge-pack/SKILL.md) may research, scaffold and validate new immutable candidate pack versions, but it is not available to the runtime agent and cannot approve, publish for runtime, or embed LOB/jurisdiction facts in its own instructions.

Every skill must declare:

- trigger and non-trigger conditions;
- purpose and scope;
- required inputs and permitted evidence;
- applicable tools and prohibitions;
- stepwise method and reasoning checkpoints;
- output contract;
- mandatory validations;
- escalation and stop conditions;
- evaluation examples; and
- version and owner.
