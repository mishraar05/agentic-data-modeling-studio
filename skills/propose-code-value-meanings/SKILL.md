---
name: propose-code-value-meanings
description: >-
  SA2 — map the observed values of a coded/enumerated source attribute to
  meanings from a governed code set, using the attribute's profile value
  distribution. Every proposed mapping cites a governed code and a profile
  frequency; values with no governed match are flagged UNMAPPED via
  unknown_handling_state — never invented, and unknown/missing/invalid/withheld
  are never collapsed together. Use when an attribute is coded and has a profile
  distribution. Do NOT use for free-text/continuous attributes, when no profile
  exists, or to invent code values or business definitions (that is SA1).
---

# SA2 — Propose Code-Value Meanings

## Status and authority

Version: `0.1.0-DRAFT`
Owner: Source Data Analyst capability owner (`TBD`)
Status: `DRAFT_PENDING_EVALUATION_GATE` — not authoritative until it passes its
evaluation examples on unseen, independently labelled coded attributes
(Charter §7). Contains **no answer keys**.

Procedural playbook only. The governed code sets themselves live in the pack and
arrive as evidence; this Skill explains how to apply them, never embeds them
(Architecture §7).

## Trigger / non-trigger

**Trigger:** an attribute is enumerated/coded (low, stable distinct set;
code-like values) **and** has an approved `profile_evidence` value distribution.

**Non-trigger:** free-text or continuous attributes; no profile available; the
attribute needs a business name/definition only (SA1) or a privacy class (SA3).

## Required inputs and permitted evidence

- The attribute's `profile_evidence` value distribution (values + frequencies).
- The contract-owned `evidence_state` and `unknown_handling_state` vocabularies.
- Governed code sets for the scope (via the fail-closed selector), referenced by
  exact `governed_code_ref` (pack/version/code_set/fingerprint/code).
- Existing-document value hints, only if admitted with citations.

## Applicable tools and prohibitions

- **Read-only** over profiles and the approved code sets.
- **May not** invent a code value, a code meaning, or a governed code that is not
  in the selected set.
- **May not** collapse `UNKNOWN` / `MISSING` / `INVALID` / `WITHHELD` / `UNMAPPED`
  into one another — each is a distinct `unknown_handling_state`.
- Writes only draft value-mapping claims and `open_question` records.

## Method (stepwise, with reasoning checkpoints)

1. **Confirm the attribute is in scope for coding.** Check the distinct-value set
   is small/stable and code-like. *Checkpoint:* if it looks free-text/continuous
   or has no profile, stop — this is not an SA2 case.

2. **Load the candidate governed code set(s)** for the attribute's subject area
   via the selector. Record the exact `governed_code_ref` for each.

3. **Match observed values to governed codes.** For each observed value in the
   distribution, find a governed code whose identity/synonyms it matches. A valid
   mapping requires **both** a governed code and a profile frequency for that value.

4. **Classify residuals explicitly.** Every observed value with no governed match
   is flagged `UNMAPPED`. Sentinel/blank/placeholder values are classified into the
   correct `unknown_handling_state` (`MISSING`, `INVALID`, `WITHHELD`, `UNKNOWN`) —
   never guessed into a real meaning. *Checkpoint:* never silently drop a value.

5. **Detect conflict.** If the distribution contains values the governed set says
   should not occur, or the governed set expects values absent from the data,
   raise an `open_question` rather than forcing a mapping.

## Output contract

Draft value-to-meaning proposals for the attribute, each a `semantic_claim` of
`value_type: CODE_VALUE` carrying a `governed_code_ref` and citing the profile
frequency as evidence. Residual values carried as `unknown_handling_state`
entries (e.g. `UNMAPPED`). `open_question` records for conflicts.

## Mandatory validations

- Every proposed mapping cites **a governed code and a profile frequency**.
- No invented code value or meaning.
- Residual values explicitly stated as `UNMAPPED`; sentinel classes not merged.
- `governed_code_ref` is exact (pack/version/code_set/fingerprint/code).
- Coverage: every value in the distribution is either mapped or explicitly handled.

## Escalation and stop conditions

- Stop and raise an `open_question` when the distribution conflicts with the
  governed code set, or when two governed sets plausibly apply.
- Defer to SA1 for the attribute's business name/definition; to SA3 for privacy.
- Stop if no profile distribution is available (record the degraded run mode).

## Evaluation

Measured on unseen coded attributes (Charter §7): mapping accuracy, `UNMAPPED`
recall (does it catch values with no governed home?), and correct
`unknown_handling_state` separation. No evaluation answers embedded here.

## Depends on

`code_set` + `governed_code_ref` contracts; a runtime-eligible pack with the
relevant code sets; **value-distribution profiling** (note: current profiling
policy `D23-03/04` permits counts-only for the synthetic-dev slice, so SA2's
distribution input is gated until a value-distribution profiling policy is approved).
