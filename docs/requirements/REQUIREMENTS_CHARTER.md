# Agentic Data Analyst and Modeler — Requirements Charter

**Status:** Controlling product requirements charter  
**Effective date:** 2026-07-15  
**Owner direction:** Modeling and STTM by line of business (LOB) and domain  
**Change control:** A material change to the goal, scope, deliverables, or principles requires an explicit owner decision. Phase plans and implementation notes cannot override this charter.  
**Related architecture:** [`AGENT_SOLUTION_ARCHITECTURE.md`](../architecture/AGENT_SOLUTION_ARCHITECTURE.md)

## 1. North-star goal

Build a reliable, fit-for-purpose **Agentic Data Analyst and Modeler** that analyzes poorly documented source data estates and creates evidence-backed, scalable:

1. reconstructed source data dictionaries;
2. Silver Operational Data Store (ODS) models;
3. Gold dimensional models; and
4. source-to-target mappings (STTMs)

for a selected LOB and business domain.

The created models must preserve the analytical intent of existing reporting requirements and support explicitly supplied new analytical requirements. Every material target-model element and mapping must be traceable to source evidence, an approved governed input, or a recorded human decision.

The system creates real project artifacts. Before review they are `DRAFT`; after authorized human approval they become `APPROVED` project deliverables. The word “recommendation” must not be used as a substitute for the solution's actual purpose: creating target models and mappings.

## 2. Problem being solved

Modernization and conversion teams commonly begin with:

- legacy schemas with no reliable source data dictionary;
- incomplete or missing lineage from reports to operational sources;
- business rules embedded in people, SQL, reports, or undocumented processes;
- inconsistent definitions and duplicated calculations;
- pressure to agree a scalable Silver ODS and Gold dimensional model early; and
- a need to support existing reports while enabling new analytics.

This solution reduces the analysis and modeling effort, uncertainty, inconsistency, and rework involved in reaching an approved target model and STTM.

## 3. Current solution scope

### In scope now

- One explicitly selected LOB and domain per bounded execution slice.
- Source metadata, controlled profiles, existing documentation, supplied reporting requirements, and new analytical requirements.
- Reconstruction of a usable source understanding where documentation is absent.
- Creation of a reviewable source data dictionary for every in-scope source object and attribute.
- Source entity, attribute, key, relationship, code-set, and semantic analysis needed for modeling.
- Creation of Silver ODS entities, attributes, keys, relationships, grain, history, standardization, privacy, and data-quality design.
- Creation of Gold facts, dimensions, grain, measures, conformed dimensions, history, and requirement coverage.
- Creation of attribute-level STTMs, transformations, joins, lookups, defaults, exceptions, data-quality rules, lineage, and reconciliation criteria.
- Evidence, assumptions, contradictions, open questions, confidence components, versioning, review, and approval.
- Human-in-the-loop review through durable tables, portable Excel workbooks, and a Databricks App.

### Deferred, but architecturally open

- Native parsing and conversion of Informatica, Talend, SSIS, or other proprietary ETL project formats.
- Automated reverse engineering of every BI/reporting tool.
- Generation or execution of migration pipelines.
- Physical deployment of Silver or Gold schemas.
- Automated production cutover or reconciliation execution.

Deferred capabilities must be addable later through versioned evidence adapters and tools. Core model contracts must not depend on a specific ETL, BI, source, or target vendor.

### Explicitly not a deliverable

- Ontology creation or ontology governance.

An ontology, enterprise glossary, canonical model, authorized product model, KPI catalog, and modeling standards are governed **inputs** when available. The solution may report a terminology conflict or missing governed concept, but it must not silently create an ontology to fill the gap.

## 4. Required inputs

The solution operates with the evidence that an engagement is authorized to provide:

- source catalog, schema, table, column, key, constraint, index, and view metadata;
- minimized and approved source profiles;
- available source dictionaries and design documents;
- supplied report inventory, metric definitions, report-to-source knowledge, and reporting requirements;
- new analytical use cases and acceptance criteria;
- approved ontology, glossary, canonical model, standards, privacy rules, and KPI definitions;
- prior approved modeling decisions for the same engagement and scope; and
- human answers to unresolved questions.

When tool-specific conversion is added later, ETL mappings, report definitions, SQL, stored procedures, and semantic-layer assets enter through separate evidence adapters. Their absence must not prevent the current modeling and STTM workflow from operating on provided evidence.

## 5. Authoritative deliverables and formats

Delta tables are the authoritative system of record. Excel and the Databricks App are review and consumption surfaces; neither becomes a second source of truth.

| Deliverable | Minimum content | Authoritative format | Review/portable format |
|---|---|---|---|
| Reconstructed Source Data Dictionary | Object and attribute definitions, physical metadata, business meaning, domain/LOB, keys, relationships, code sets, profiles, privacy, evidence, confidence, assumptions, contradictions, questions, and approval | Versioned Delta tables and validated JSON contracts | Dedicated Excel workbook/sheets + Databricks App |
| Silver ODS model | Entities, attributes, grain, keys, relationships, types, history, privacy, data quality, source coverage | Versioned Delta tables and validated JSON contracts | Excel model workbook + diagrams + App |
| Gold dimensional model | Facts, dimensions, grain, measures, conformance, SCD behavior, requirement coverage | Versioned Delta tables and validated JSON contracts | Excel model workbook + diagrams + App |
| STTM package | Source/target fields, transformation logic, joins, lookups, defaults, exceptions, DQ rules, evidence, lineage, reconciliation | Versioned Delta tables and validated JSON contracts | Excel STTM workbook + App |
| Requirement coverage matrix | Existing and new requirement to Gold/Silver/model-element coverage | Versioned Delta table | Excel + App |
| Decision and gap register | Contradictions, open questions, decisions, rationale, owner, impact, status | Append-only Delta tables | App review queue + Excel export |
| Run evidence | Context snapshot, model/prompt/skill versions, tool calls, traces, validation, cost, latency | MLflow traces plus Delta run records | App operational view |

Every Excel workbook must be generated from the authoritative records and carry engagement, scope, version, run, approval status, and generation timestamp. It must never be independently edited and re-imported without a controlled decision-ingestion process.

### 5.1 Source Data Dictionary contract

The Source Data Dictionary is a primary project deliverable, not merely an intermediate agent artifact. It must cover every in-scope source object and attribute and preserve the distinction between observed source facts and inferred business meaning.

At minimum it contains:

| Field group | Required contents |
|---|---|
| Scope and identity | Engagement, source system, product/module/version when known, LOB, domain, schema, object, attribute, ordinal position |
| Physical definition | Source type, length, precision, scale, nullability, default, constraint, index, observed key role |
| Business definition | Proposed business name, plain-language definition, business purpose, synonyms, subject area, lifecycle/status meaning |
| Values and profiling | Approved code/value meanings, null/distinct statistics, formats, ranges, patterns, and profile snapshot reference |
| Relationships | Primary/alternate/foreign-key role, parent/child object, cardinality, relationship evidence, and validation status |
| Governance | Privacy/sensitivity class, retention or handling rule when supplied, owner, steward, reviewer, and approval state |
| Trust | Observed/inferred/unresolved state, evidence references, confidence components, assumptions, contradictions, and open questions |
| Lineage and reproducibility | Metadata/profile query reference, context snapshot, run ID, model/prompt/skill versions, artifact version, and timestamps |

Required quality gates:

- 100% inventory coverage for in-scope objects and attributes;
- no inferred meaning represented as an observed fact;
- no invented code value, key, relationship, or business definition;
- every inferred definition cites evidence or an approved human decision;
- ambiguous and opaque fields remain visibly unresolved;
- every key, privacy classification, and material relationship is reviewed; and
- approved reviewer modifications are retained as durable context for later Silver, Gold, and STTM work.

### 5.2 Logical table families

Physical schemas will be defined by versioned contracts, but the authoritative model must include these logical record families:

| Family | Logical records |
|---|---|
| Run and scope | `engagement`, `work_package`, `solution_run`, `context_snapshot`, `artifact_version` |
| Evidence | `evidence_item`, `source_object_observation`, `source_attribute_observation`, `profile_evidence`, `relationship_candidate` |
| Requirements | `analytical_requirement`, `reporting_requirement`, `business_term`, `business_rule` |
| Silver | `silver_entity`, `silver_attribute`, `silver_relationship`, `silver_history_rule`, `silver_data_quality_rule` |
| Gold | `gold_fact`, `gold_dimension`, `gold_measure`, `gold_relationship`, `gold_conformance_rule` |
| Mapping | `mapping_package`, `attribute_mapping`, `transformation_rule`, `lookup_rule`, `reconciliation_rule` |
| Coverage and lineage | `requirement_coverage`, `artifact_dependency`, `lineage_edge` |
| Governance | `validation_finding`, `review_item`, `review_decision`, `open_question` |

All records require stable identities, engagement and LOB/domain scope, version, lifecycle state, provenance, and timestamps. Semantic records additionally require evidence references, assumptions, and unresolved contradictions.

### 5.3 Excel workbook contract

The portable workbook must contain, where applicable:

1. Cover and approval status;
2. scope and inputs;
3. Source Data Dictionary — objects;
4. Source Data Dictionary — attributes;
5. source relationships, code values, and profiles;
6. Silver entities, attributes, relationships, history, and data quality;
7. Gold facts, dimensions, measures, grain, and conformance;
8. source-to-Silver STTM;
9. Silver-to-Gold STTM;
10. business and transformation rules;
11. existing and new requirement coverage;
12. evidence and lineage references;
13. assumptions, contradictions, and open questions; and
14. review decisions and change history.

### 5.4 Databricks App contract

The review application must provide:

- engagement/run dashboard and scope lock;
- dedicated Source Data Dictionary view with object/attribute search, filters, evidence drill-through, and review status;
- source-evidence, relationship, code-value, and profile exploration;
- Silver and Gold model views with version comparison;
- searchable and filterable STTM grids;
- requirement coverage and gap views;
- evidence drill-through for every material model element;
- role-based review, modification, rejection, deferral, and approval;
- impact analysis before accepting a material change;
- Excel export generated from the selected artifact version; and
- run, trace, cost, latency, and validation status.

## 6. Solution constraints and non-functional requirements

The solution shall:

- use LLMs and agents for semantic interpretation, synthesis, critique, and modeling judgment;
- prohibit hard-coded expected semantic answers used to simulate agent quality or determinism;
- use deterministic code for security, exact calculations, contracts, validation, workflow state, and policy enforcement;
- maintain evidence traceability for every material inferred definition, model element, and mapping;
- separate source facts, governed inputs, requirements, inferences, and human decisions;
- prevent automatic approval of material model artifacts;
- isolate engagements and enforce least-privilege access;
- reproduce outputs from versioned evidence, context, model, prompt, skill, and configuration snapshots, or explain controlled model variance;
- remain extensible through adapters without depending on one source, ETL, BI, or target vendor; and
- meet agreed quality, cost, latency, recovery, security, and reviewer-effort thresholds.

Detailed agent, context, guardrail, harness, technology, and skill decisions are defined in [`AGENT_SOLUTION_ARCHITECTURE.md`](../architecture/AGENT_SOLUTION_ARCHITECTURE.md).

## 7. Fit-for-purpose success measures

The solution is successful only when a bounded LOB/domain slice demonstrates:

| Measure | Required direction |
|---|---|
| Evidence traceability | 100% of material model and STTM elements cite evidence, a requirement, or an approved decision |
| Source Data Dictionary coverage | 100% of in-scope objects and attributes are documented or explicitly unresolved |
| Source Data Dictionary quality | Definitions, keys, relationships, code values, and privacy classes meet independently reviewed accuracy targets |
| Existing requirement coverage | All agreed in-scope existing requirements are mapped, intentionally retired, or explicitly unresolved |
| New analytical requirement coverage | All agreed new requirements trace to Gold measures/dimensions and supporting Silver elements |
| Model quality | Grain, keys, history, relationships, conformance, and naming pass architect-approved checks |
| Mapping completeness | Required target attributes have source, derivation, default, or documented gap |
| Semantic quality | Measured on unseen, independently labelled cases; no evaluation-set answer keys in rules |
| Reviewer effort | Lower than the documented manual baseline without reducing quality |
| Reviewer override rate | Measured by artifact type and reduced through learning from approved decisions |
| Reproducibility | Same versioned evidence/context/model/skill configuration reproduces the artifact or explains controlled variance |
| Operational fitness | Cost, latency, recovery, security, and monitoring meet agreed pilot thresholds |

Passing unit tests or producing a large ontology does not prove this goal.

## 8. Anti-drift rules

Before starting any work package, answer:

1. Which charter deliverable does this create or improve?
2. Which selected LOB/domain and requirement does it serve?
3. What evidence will prove that it improves modeling or STTM quality, coverage, or effort?
4. Is this genuinely required now, or only future extensibility?
5. Should this be an agent, a skill, a tool, a deterministic validator, or governed context?

Stop or rescope work that cannot answer the first three questions.

The precedence order is:

1. this Requirements Charter;
2. approved deliverable contracts;
3. the Agent Solution Architecture and architecture decisions;
4. evaluation and acceptance criteria;
5. work-package plans;
6. implementation details.

## 9. Next proof slice

Choose one LOB/domain and a small connected subject area. Supply:

- source metadata and approved profiles;
- a bounded set of existing reporting requirements;
- at least one new analytical requirement;
- approved modeling standards and ontology/glossary inputs if available; and
- an independent architect/SME review baseline.

The slice is complete only when it produces and reviews the reconstructed Source Data Dictionary, Silver ODS model, Gold dimensional model, STTM, coverage matrix, gaps, and run evidence through the defined formats.

