---
name: analyze-source-subject-area
description: >-
  SA1 — the Source Data Analyst's core reasoning playbook. Propose business
  meaning (name, definition, purpose, subject area, synonyms, lifecycle meaning)
  for one in-scope source object and its attributes, from an assembled Phase 1-2
  evidence bundle plus governed context. Every claim is tagged
  OBSERVED/INFERRED/DECIDED/UNRESOLVED; anything not OBSERVED cites evidence or a
  human decision; insufficient evidence becomes an open question, never a guess.
  Use when an object/attribute slice has its evidence bundle ready. Do NOT use to
  read raw source rows, map coded values (SA2), finalize privacy (SA3), invent
  fields/meanings, or approve anything.
---

# SA1 — Analyze Source Subject Area

## Status and authority

Version: `0.1.0-DRAFT`
Owner: Source Data Analyst capability owner (`TBD`)
Status: `DRAFT_PENDING_EVALUATION_GATE` — not authoritative until it passes its
evaluation examples on unseen, independently labelled cases (Charter §7). This
file contains **no answer keys**; the examples below illustrate behavior/format,
not graded answers.

Authority order: Requirements Charter → approved contracts → Agent Solution
Architecture + ADRs → this Skill. Stop on conflict; never repair a
higher-authority artifact from here.

This is a **procedural playbook**, not a fact store. LOB/domain facts, glossary,
code sets and engagement decisions live in governed context and arrive as
evidence — this Skill only explains how to retrieve and apply them (Architecture §7).

## Trigger / non-trigger

**Trigger:** an in-scope object/attribute slice has its Phase 1-2 evidence bundle
assembled (`source_object_observation`, `source_attribute_observation`,
`profile_evidence`, `relationship_candidate`) and a runtime-eligible governed
pack is selected for scope.

**Non-trigger:** evidence not yet ingested; the slice is outside the allow-listed
source boundary; the attribute needs coded-value mapping only (use SA2) or a
privacy decision only (use SA3).

## Required inputs and permitted evidence

- `source_object_observation`, `source_attribute_observation` — physical facts.
- `profile_evidence` — null/distinct/among approved profile statistics, when available.
- `relationship_candidate` — declared and heuristic keys/relationships.
- Scoped governed glossary / domain / standards from the selected pack (via the
  fail-closed selector), referenced by exact pack/version/fingerprint.
- Prior `review_decision`s for this engagement/object scope (episodic memory).
- Existing-document fragments, only if admitted through an evidence adapter with citations.

Permitted evidence is exactly what arrives in the bounded context envelope. Never
scan directories, pull whole repositories, or read source data values.

## Applicable tools and prohibitions

- **Read-only** over the evidence stores and the approved pack (fail-closed selector).
- **May not** invent an object, attribute, field, code value, key, relationship,
  or evidence reference.
- **May not** finalize a privacy class (route to SA3/steward) or set any `APPROVED` state.
- **May not** mark a value `OBSERVED` without a Phase-1 evidence item behind it.
- Writes only draft dictionary claims and `open_question` records.

## Method (stepwise, with reasoning checkpoints)

1. **Assemble the per-object bundle.** Gather the object observation, its
   attribute observations (ordered by ordinal), profile summaries, surfaced
   relationship candidates, the scoped glossary/domain slice, and any prior
   decisions for this object. *Checkpoint:* if the pack slice or evidence is
   missing, stop — do not proceed from background knowledge.

2. **Object-level meaning.** Propose a candidate business `name`, `definition`,
   `purpose`, `subject_area`, and `synonyms` for the object. Ground each in cited
   evidence: physical structure, key role, relationship candidates, report
   linkage, and governed glossary matches. *Checkpoint:* for each field ask "what
   evidence supports this?" If only the physical name suggests it and nothing
   corroborates, that is weak — prefer `UNRESOLVED` over a confident guess.

3. **Attribute-level meaning.** For each attribute propose `business_name`,
   `business_definition`, `purpose`, `synonyms`, and `lifecycle_meaning`. Use the
   column name, datatype, nullability, key role, profile shape, and glossary
   matches as evidence. Key-bearing attributes get meaning **added to** the
   structural candidate — meaning never replaces structural evidence.

4. **Tag every claim with a trust state:**
   - `OBSERVED` — directly present in source evidence (cite `evidence_item`(s)).
   - `INFERRED` — a supported conclusion (cite `evidence_item`(s) + confidence components).
   - `DECIDED` — established by an authorized human decision (cite the `review_decision`).
   - `UNRESOLVED` — evidence insufficient or contradictory (emit an `open_question`, no value).

5. **Reconcile with prior decisions.** If a prior `review_decision` covers a
   field, reuse it as `DECIDED` rather than re-inferring. Do not contradict an
   approved decision silently — if new evidence conflicts, raise an `open_question`.

6. **Insufficient evidence → ask, never guess.** Any field lacking adequate
   support becomes `UNRESOLVED` + a scoped, answerable `open_question` naming what
   evidence would resolve it.

7. **Flag, don't finalize, cross-cutting concerns.** Privacy-looking attributes
   are handed to SA3 (candidate only). Coded/enumerated attributes are handed to
   SA2. Cross-object contradictions are routed to the critic (CR1).

## Output contract

Draft `source_dictionary_object` / `source_dictionary_attribute` records whose
`business_*` fields are contract `semantic_claim`s, each with:
`evidence_state`, and — for non-`OBSERVED` — `evidence_refs` (+ `confidence` for
`INFERRED`) or a `review_decision_ref` (for `DECIDED`) or an `open_question_ref`
(for `UNRESOLVED`). Records are `DRAFT`; nothing is approved here. Plus
`open_question` records for every `UNRESOLVED` field.

## Mandatory validations

- No `INFERRED` claim without at least one cited `evidence_item`.
- No claim marked `OBSERVED` without a Phase-1 evidence item.
- Insufficient/contradictory evidence yields `UNRESOLVED` + `open_question` (no value).
- No invented object, attribute, key, relationship, or evidence reference.
- Governed vocabulary referenced by exact pack/version/fingerprint, never copied inline.
- Every in-scope object/attribute has a record (100% coverage; `UNRESOLVED` counts).

## Escalation and stop conditions

- Emit `UNRESOLVED` rather than guess.
- Route candidate privacy to SA3/steward; route coded values to SA2.
- Route cross-object contradictions to CR1.
- Stop and raise if the pack slice is missing, evidence is absent, or the request
  falls outside the allow-listed boundary.

## Evaluation

Measured on **unseen, independently labelled** objects/attributes (Charter §7):
name/definition accuracy, correct trust-state assignment, appropriate
`UNRESOLVED` rate (neither over-guessing nor over-deferring), and citation
coverage. No evaluation-set answers may be embedded in this Skill.

*Illustrative behavior (not a graded key):* a column with a declared primary-key
constraint and an unambiguous glossary match → `INFERRED` name/definition citing
both. A column named `col_9` with no corroborating evidence → `UNRESOLVED` +
open_question. A field a reviewer already approved last run → `DECIDED` citing the
prior `review_decision`.

## Depends on

SDD evidence + dictionary + open_question contracts; a runtime-eligible governed
pack; the context assembler + episodic read-path (ADR-006). Without these the
positive path cannot execute.
