# Review and evaluation

## Review routing

| Content | Required reviewer |
|---|---|
| Cross-LOB insurance semantics | Domain SME and knowledge owner |
| LOB product/risk/coverage/lifecycle semantics | LOB SME |
| Jurisdiction obligations, thresholds, applicability and dates | Regulatory/compliance reviewer; legal counsel for unresolved high-impact interpretation |
| KPIs, premium/loss/accounting semantics | Finance/actuarial/KPI owner |
| Privacy/retention rules | Privacy steward |
| Proprietary or copyrighted sources | Licensing/content-rights owner |
| Modeling standards/reference alignment | Data architect |

No reviewer role may be silently replaced by an LLM.

## Completeness scoring

- Define dimensions and weights before researching; weights must total 100.
- Score evidenced coverage, not volume, folders, terms or source count.
- Give no SME/evaluation credit without named completed review.
- Give no licensed-content credit without authorization.
- Recompute the weighted score deterministically.
- Report each dimension and gap; never hide a zero behind the aggregate.
- Keep trusted-runtime readiness separate from content completeness.

## Acceptance gates

- all declared paths and fingerprints validate;
- all source IDs resolve and are unique;
- every new material claim has claim-level provenance;
- jurisdiction claims have applicability and effective-date status;
- no protected content is reproduced without permission;
- no ontology creation or source-specific engagement artifact is present;
- critic findings and reviewer decisions are recorded;
- the pack remains candidate/non-runtime until formal promotion; and
- unseen forward evaluation demonstrates generalization.

## Forward evaluation

Test at least two independent axes:

1. a different LOB with no access to the reference pack's expected answers; and
2. a different jurisdiction for an existing LOB, using current primary sources.

Measure structural validity, source precision, claim-level citation coverage, jurisdiction leakage, contradiction recall, completeness calibration, reviewer corrections and unsupported-claim rate. Include adversarial missing/contradictory/expired/licence-restricted sources. Reject a skill revision that passes only by copying Personal Auto or California structure/content mechanically.

