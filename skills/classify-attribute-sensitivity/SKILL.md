---
name: classify-attribute-sensitivity
description: >-
  SA3 — propose a CANDIDATE privacy/sensitivity classification for a source
  attribute that matches a privacy-relevant signal (personal name, address, date
  of birth, government or tax ID, contact details, etc.), citing governed privacy
  guidance. It ALWAYS routes the candidate to a privacy steward and NEVER
  finalizes a class; false negatives are treated as high-cost. Use when an
  attribute shows a sensitivity signal. Do NOT use to finalize/approve a privacy
  class, to read raw sensitive values, or for business meaning (SA1) or coded
  values (SA2).
---

# SA3 — Classify Attribute Sensitivity

## Status and authority

Version: `0.1.0-DRAFT`
Owner: Source Data Analyst capability owner + privacy governance owner (`TBD`)
Status: `DRAFT_PENDING_EVALUATION_GATE` — not authoritative until it passes its
evaluation examples on unseen, independently labelled attributes (Charter §7).
Contains **no answer keys**.

Procedural playbook only. Governed privacy guidance lives in the pack and arrives
as evidence; this Skill applies it, never embeds it (Architecture §7).

## Trigger / non-trigger

**Trigger:** an attribute matches a privacy-relevant pattern by name, type, or
profile shape (e.g. given/family name, full name, address, DOB/birth date, SSN/
national/tax ID, passport, driver-licence, email, phone).

**Non-trigger:** no sensitivity signal; or the attribute's privacy class is
already `DECIDED` by a steward for this scope; or the request is for business
meaning (SA1) or coded-value mapping (SA2).

## Required inputs and permitted evidence

- The attribute's name, data type, key role, and **profile pattern metadata**
  (formats/patterns) — not raw values.
- Governed privacy/sensitivity guidance from the selected pack (via the selector),
  referenced by exact `governed_code_ref`.
- Prior steward `review_decision`s for this attribute/scope.

## Applicable tools and prohibitions

- **Read-only.** Never reads or retains raw sensitive values.
- **ALWAYS routes** the candidate to `privacy_steward`.
- **MAY NEVER finalize** a privacy class, set `APPROVED`, or suppress its own finding.
- Writes only a candidate classification (pending steward review) and, where
  needed, an `open_question`.

## Method (stepwise, with reasoning checkpoints)

1. **Detect the signal.** From name/type/pattern metadata, identify the candidate
   sensitivity category. *Checkpoint:* use pattern metadata only — never inspect raw values.

2. **Map to governed guidance.** Select the governed sensitivity class the signal
   corresponds to and record its exact `governed_code_ref`. If several plausibly
   apply, keep the **most protective** and note the alternatives.

3. **Emit a candidate, never a decision.** Produce a candidate class marked
   *pending steward review*, citing the governed guidance and the detection signal.

4. **Attach steward routing.** Every candidate is routed to `privacy_steward`; the
   attribute's privacy field stays non-final until the steward decides.

5. **Escalate the ambiguous and the high-risk.** Any ambiguous or high-impact
   match (e.g. possible government ID) escalates to the steward with the evidence,
   and — where the class is genuinely undetermined — raises an `open_question`.
   *Checkpoint:* bias toward flagging; a missed sensitive attribute is worse than
   a false alarm.

## Output contract

A **candidate** `privacy_class` `semantic_claim` (`value_type: PRIVACY_CLASS`)
carrying a `governed_code_ref`, marked pending steward review, with the detection
signal cited. The dictionary attribute's privacy field remains non-final. Steward
routing metadata attached; `open_question` for undetermined cases.

## Mandatory validations

- Candidate cites governed privacy guidance (`governed_code_ref`, exact).
- Steward-review routing is attached; the class is **non-final**.
- No raw sensitive value is read or retained.
- Ambiguous/high-risk matches are escalated, not resolved in place.

## Escalation and stop conditions

- Route every candidate to the steward; never finalize.
- Escalate ambiguous/high-risk matches with evidence.
- Defer business meaning to SA1 and coded values to SA2.
- Stop if governed privacy guidance is not available in the selected pack (record
  the gap; do not classify from background knowledge).

## Evaluation

Measured on unseen, SME-labelled attributes (Charter §7): precision and recall
against labelled sensitive attributes, with **false negatives weighted high**.
No evaluation answers embedded here.

## Depends on

Governed privacy guidance in a runtime-eligible pack; the `PRIVACY_CLASS`
`semantic_claim` + `governed_code_ref` contracts; a defined `privacy_steward`
review path.
