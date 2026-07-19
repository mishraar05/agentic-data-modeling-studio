# Metadata contract inventory

The framework has **29 record contracts** plus `_common.schema.json`. Records are
bounded by one solution run and, when semantic judgment is involved, an immutable
context snapshot. There are no separate client-engagement or work-decomposition
identity columns.

## Control and immutable context

`solution_run`, `artifact_version`, `source_snapshot`, `context_snapshot`,
`profile_snapshot`, `document_set`, `requirement_set`, and `evidence_set`.

## Evidence and AI analysis

`evidence_item`, `source_object_observation`, `source_attribute_observation`,
`profile_evidence`, and `relationship_candidate`.

The relationship candidate is a reviewable material artifact. An LLM may propose
it, an independent critic assesses it, deterministic guards validate its citations
and scope, and only a review decision can approve it.

## Requirements and business semantics

`analytical_requirement`, `reporting_requirement`, `business_term`, and
`business_rule`.

## Reconstructed Source Data Dictionary

`source_dictionary_attribute`, `source_dictionary_object`,
`source_dictionary_relationship`, and `source_dictionary_code_value`.

## Governance, traceability, and handoff

`validation_finding`, `review_item`, `review_decision`, `open_question`,
`artifact_dependency`, `lineage_edge`, `source_dictionary_handoff`, and
`skill_resolution`.

## Shared rules

All contracts reference `common:0.4.0`. The common envelope carries record,
LOB/domain, lifecycle, provenance, and timestamps. Base provenance requires
`run_id`; context-dependent records additionally require `context_snapshot_id`.
Observed and inferred claims must cite evidence. Approved material records require
a human review-decision reference.
