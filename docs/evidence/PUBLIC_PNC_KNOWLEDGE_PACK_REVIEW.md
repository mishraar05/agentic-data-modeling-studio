# Public P&C knowledge pack — candidate review

**Status:** Candidate; not approved for trusted agent retrieval  
**Prepared:** 2026-07-15  
**Scope:** Cross-LOB Policy and Claims foundation plus Personal Auto  
**Charter deliverables advanced:** Source Data Dictionary, Silver ODS, Gold dimensional model, and STTM  

## Purpose

This pack supplies bounded vocabulary and modeling questions that can improve semantic analysis. It does not contain client evidence, create an ontology, prescribe a target model, or replace SME decisions. Source observations remain authoritative for physical facts; approved engagement knowledge and human decisions take precedence for business meaning.

## Admission decision

| Source | Admission | Reason |
|---|---|---|
| EDMC FIBO repository | Candidate open reference | Official repository identifies an MIT license; exact release and concepts still require ontology-owner selection. |
| NAIC public consumer/glossary pages | Link and independent paraphrase only | No open-content license was identified. Do not copy definitions or enable production retrieval until legal/knowledge-owner review. |
| Databricks documentation | Candidate technical reference | Official platform guidance, independently paraphrased; enterprise modeling standards still require architect approval. |

## Required reviewers

- P&C domain steward: terminology, relationships, and Personal Auto scope.
- Data architect: Silver/Gold standards, grain, history, and model neutrality.
- Knowledge owner: pack boundaries, precedence, effective dates, and runtime eligibility.
- Legal/licensing reviewer: NAIC reference and paraphrase policy before production use.

## Acceptance checks

1. No copied third-party definition or proprietary schema is present.
2. Every concept is marked candidate and retains source provenance.
3. Jurisdiction-dependent terms remain explicitly unresolved.
4. The pack cannot override client evidence or approved enterprise knowledge.
5. Runtime retrieval remains disabled until the manifest is approved and registered.
6. A proof-slice evaluation measures whether the pack improves independently reviewed dictionary, model, and STTM quality without increasing unsupported inference.

## Explicit exclusions

- Guidewire schemas, data models, and proprietary product documentation.
- ACORD standards content unless separately licensed and supplied by the owner.
- Vendor blogs, community posts, generated websites, and unattributed glossaries.
- Code sets, KPI formulas, jurisdictional rules, and target reference models not yet governed.
