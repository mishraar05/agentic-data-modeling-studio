# Knowledge layer — 90% production-grade acceptance plan

**Goal:** Reach at least 90% scoped content completeness and separately satisfy production trust gates for the US Personal Auto Policy and Claims knowledge layer.  
**Current approved runtime pack:** `public_us_pnc_personal_auto` `v0.6.0`; its retained readiness score remains the baseline for the improvement plan.  
**Current baseline:** 75% content completeness; 0% trusted-runtime readiness.  
**Controlling principle:** Scores cannot be increased by folder count, duplicated terms, corrected defects alone, or unreviewed internet content.

## Production-grade definition

A pack is production grade only when it is sufficiently comprehensive for its declared jurisdiction and product scope, correctly sourced, licensed for its intended use, reviewed by accountable SMEs, evaluated on unseen source estates, and enforced by runtime guardrails. Content completeness and trusted-runtime readiness are separate measures; both must meet the agreed threshold.

## Current dimension assessment

| Dimension | Weight | Current | Production target |
|---|---:|---:|---:|
| Governance and provenance | 10% | 82% | 100% |
| Core glossary | 15% | 82% | 95% |
| Policy domain | 15% | 80% | 92% |
| Claims domain | 15% | 84% | 92% |
| Personal Auto LOB | 15% | 82% | 92% |
| Silver/Gold/STTM standards | 10% | 82% | 90% |
| KPI catalog and code sets | 10% | 70% | 90% |
| Reference alignment | 5% | 45% | 80% |
| Expert validation and evaluation | 5% | 0% | 85% |

The weighted current score is 74.85%, rounded to 75%. No dimension is hidden by the aggregate score.

## Completed candidate increments

- `v0.4.0`: corrected California legal semantics and immutable source governance; score remained 55%.
- `v0.5.0`: expanded the Policy–Risk–Coverage–Claims semantic spine and regulator-aligned KPI contexts; score reached 65%.
- `v0.6.0`: added Party/PII, Billing/premium, total-loss/recovery, glossary, semantic code-set, pinned reference, and detailed modeling/STTM contracts; score reached 75%.

## Remaining candidate content work

1. Complete candidate financial KPI contracts for exposure earning incurred loss expense allocation severity frequency loss ratio and combined ratio.
2. Add licensed or client-authorized Personal Auto forms product variants underwriting/rating definitions and carrier code values.
3. Select and approve exact FIBO concepts and an authorized target reference model.
4. Add enterprise-approved physical naming data types DQ tolerances privacy retention and financial reconciliation rules.
5. Add remaining California product and operational detail only from authoritative sources and legal review.

## Inputs required to cross the production-grade boundary

- Named knowledge owner, Policy SME, Claims SME, Personal Auto product SME, data architect, privacy steward, finance SME, and legal/licensing reviewer.
- Authorized enterprise glossary, product/forms knowledge, source code sets, KPI definitions, accounting policy, and target-reference inputs.
- A representative unseen legacy source slice, approved profiles, existing reports, and at least one new analytical requirement.
- Independent review results and measured Source Dictionary accuracy, model quality, STTM completeness, requirement coverage, reviewer effort, overrides, cost, and latency.

Public research can continue improving candidate breadth, but **90% production-grade status cannot be honestly claimed from public sources alone**. The missing enterprise evidence, licensed content, expert review, and unseen proof slice are part of the definition—not optional paperwork.
