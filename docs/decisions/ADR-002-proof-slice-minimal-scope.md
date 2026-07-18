# ADR-002: Proof-slice minimal scope vs. deferred platform layer

**Status:** Proposed
**Date:** 2026-07-18
**Decision owner:** Solution owner
**Related:** [`REQUIREMENTS_CHARTER.md`](../requirements/REQUIREMENTS_CHARTER.md) §5.2, §9; [`ADR-001`](ADR-001-canonical-knowledge-pack-structure.md)

## Context

The Requirements Charter specifies an ambitious enterprise system: ~35 first-class governed record types (§5.2), multi-tenant engagement isolation, full reproducibility and lineage infrastructure, and Delta-backed governance. None of it exists yet.

What *does* exist is disproportionate:

- ~2,800 of ~2,870 files are `knowledge/` YAML — six iterated versions (0.1.0 → 0.6.0) of P&C personal-auto knowledge packs, plus an archive. The charter classifies this content as a **governed input, never a deliverable**, and explicitly warns that "producing a large ontology does not prove this goal."
- The actual solution is three Python files: a scope-validation notebook, an empty package `__init__`, and a Streamlit stub. `contracts/`, `prompts/`, `evals/`, `skills/`, `tests/` are empty or absent.
- Two named controlling documents are missing: `docs/architecture/AGENT_SOLUTION_ARCHITECTURE.md` and `databricks.yml`.

**None of the four charter deliverables** — reconstructed Source Data Dictionary, Silver ODS model, Gold dimensional model, STTM — **and none of the agent machinery that would produce them, exists.**

Two problems compound:

1. **Drift.** Effort has gone to authoring/re-structuring input content and governance docs, not to the core capability the product is supposed to wrap.
2. **Over-engineering.** The schema is designed as a multi-tenant, fully-audited system-of-record *before* the one hard creative capability (turning messy source metadata into a reviewable, evidence-backed model) has been demonstrated once. Identifiers such as `engagement_id` and `work_package_id` presuppose concurrent client engagements and formal work decomposition that do not exist.

## Decision

Adopt a **proof-slice-minimal scope**. Build only what is required to prove the core hypothesis on ~5 source tables in one LOB/domain, then let the enterprise-platform layer earn its place with explicit re-entry criteria.

Governing test for every record, table, and identifier:

> *If I deleted this, could I still prove the agent produces a good, reviewed Source Data Dictionary and downstream model for 5 tables?* If yes, defer it.

### Proof-slice minimal schema (build now)

Roughly a dozen tables plus a `run_id` string and a version string:

**Evidence** — `evidence_item`, `source_object_observation`, `source_attribute_observation`, `profile_evidence` (if profiles supplied), `relationship_candidate`
**Requirements** — `reporting_requirement` (bounded set), `analytical_requirement` (≥1 new)
**Silver** — `silver_entity`, `silver_attribute`, `silver_relationship`
**Gold** — `gold_fact`, `gold_dimension`, `gold_measure`
**Mapping** — `attribute_mapping`, `transformation_rule` (may begin as a field on the mapping)
**Coverage** — `requirement_coverage` (simple matrix)
**Governance** — `review_item`, `review_decision`, `open_question`, `validation_finding`

Consume as **governed inputs** (do not build as tables): `business_term`, `business_rule` — these already live in the knowledge packs.

Represent as **string/column/container, not a governed table**: `run_id` (from `solution_run`), version tag (from `artifact_version`), `mapping_package`, `gold_relationship`, `lineage_edge` (derive from mappings).

### Deferred platform layer (do not build until re-entry criterion is met)

| Record / concern | Defer until |
|---|---|
| `engagement` (multi-tenant isolation) | A second concurrent engagement is real. |
| `work_package` | Work is formally decomposed across multiple teams/slices. |
| `context_snapshot`, `artifact_dependency` | An artifact has been reproduced or audited in anger. |
| `silver_history_rule` | The slice includes attributes needing SCD/history design. |
| `silver_data_quality_rule` | Modeling capability is proven; DQ becomes the next quality lever. |
| `gold_conformance_rule` | More than one fact must share conformed dimensions. |
| `lookup_rule` | The slice actually requires code-set lookups. |
| `reconciliation_rule` | Migration execution enters scope (charter already defers this). |

## Scope tags (charter §5.2, full detail)

KEEP = core to the proof · SIMPLIFY = concept needed, but as column/file/string · DEFER = real, but after the proof.

| Family | Record | Tag |
|---|---|---|
| Run & scope | `engagement` | DEFER |
| | `work_package` | DEFER |
| | `solution_run` | SIMPLIFY (`run_id`) |
| | `context_snapshot` | DEFER |
| | `artifact_version` | SIMPLIFY (version string) |
| Evidence | `evidence_item` | KEEP |
| | `source_object_observation` | KEEP |
| | `source_attribute_observation` | KEEP |
| | `profile_evidence` | KEEP (if profiles supplied) |
| | `relationship_candidate` | KEEP |
| Requirements | `reporting_requirement` | KEEP |
| | `analytical_requirement` | KEEP |
| | `business_term` | SIMPLIFY (governed input) |
| | `business_rule` | SIMPLIFY (governed input) |
| Silver | `silver_entity` | KEEP |
| | `silver_attribute` | KEEP |
| | `silver_relationship` | KEEP |
| | `silver_history_rule` | DEFER |
| | `silver_data_quality_rule` | DEFER |
| Gold | `gold_fact` | KEEP |
| | `gold_dimension` | KEEP |
| | `gold_measure` | KEEP |
| | `gold_relationship` | SIMPLIFY |
| | `gold_conformance_rule` | DEFER |
| Mapping | `attribute_mapping` | KEEP |
| | `transformation_rule` | KEEP |
| | `mapping_package` | SIMPLIFY |
| | `lookup_rule` | DEFER |
| | `reconciliation_rule` | DEFER |
| Coverage & lineage | `requirement_coverage` | KEEP |
| | `lineage_edge` | SIMPLIFY (derive) |
| | `artifact_dependency` | DEFER |
| Governance | `review_item` | KEEP |
| | `review_decision` | KEEP |
| | `open_question` | KEEP |
| | `validation_finding` | KEEP |

**Totals:** ~18 KEEP · ~7 SIMPLIFY · ~10 DEFER. The proof slice needs roughly half of the specified records; the deferred set is almost entirely the enterprise-platform layer.

## Consequences

- The next milestone is a working end-to-end slice (evidence in → deliverables out → human review), not more knowledge content or governance tables.
- Scope identifiers shrink to `run_id`, `version`, `lob`, `domain` for the proof. `engagement_id` and `work_package_id` are removed from the near-term path (including the `00_validate_scope` parameter set) and reintroduced only against the re-entry table above.
- No deferred concern is deleted from the charter's long-term intent; each has an explicit trigger, so deferral is auditable rather than lossy.
- Knowledge packs remain valid **input**. Their versioning pace should stop being treated as delivery progress.
- Risk if not adopted: continued investment in a platform skeleton around an unproven core, and a growing gap between artifact count and demonstrated capability — the exact failure the charter's anti-drift gate (§8) exists to prevent.

## Charter alignment

This ADR does not change the charter goal, deliverables, or principles; it sequences them. It applies charter §8 ("Stop or rescope work that cannot answer the first three questions") and §9 ("smallest connected subject area") to the §5.2 record set. A material change to the goal, scope, or deliverables would still require an explicit owner decision per the charter's change-control clause.
