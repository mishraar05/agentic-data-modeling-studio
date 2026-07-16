# ADR-002: First production jurisdiction — California

**Status:** Accepted  
**Date:** 2026-07-15  
**Decision owner:** Solution owner

## Context

`docs/requirements/KNOWLEDGE_PRODUCTION_GRADE_90_PLAN.md` requires a first production jurisdiction or an explicitly bounded multi-state scope. Without that decision, jurisdiction knowledge can only remain illustrative and cannot be evaluated against a concrete production boundary.

California, New York, Texas, and a bounded multi-state scope were considered. A multi-state first slice was rejected because it multiplies legal, licensing, SME, and evaluation work before one jurisdiction has passed the production gates. California and New York already had candidate public references; California also supplies a fault-based starting point while New York introduces no-fault/PIP complexity.

## Decision

California is the first production-grade Personal Auto jurisdiction scope.

Reasons:

1. Its fault-based Personal Auto liability regime is an appropriate first proof slice.
2. Proposition 103 prior-approval processes apply to Personal Auto rate filings and provide public regulatory and filing evidence through the California Department of Insurance.
3. Existing candidate material already references California Department of Insurance sources, reducing rework.
4. The scope is commercially meaningful while remaining bounded to one jurisdiction.

## Authoritative evidence

- California Department of Insurance, [Rate Filing Review Process](https://www.insurance.ca.gov/0250-insurers/0800-rate-filings/rate-filing-review-process.cfm), identifies Personal Auto as a Proposition 103 prior-approval line.
- California Insurance Code [Section 1861.05](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=INS&sectionNum=1861.05.) supplies the statutory prior-approval basis.
- California Insurance Code [Chapter 10, Sections 660–669.5](https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?article=&chapter=10.&division=1.&lawCode=INS&part=1.&title=) is the applicable cancellation and nonrenewal chapter for the Personal Auto scope.

The evidence supports jurisdiction selection only. It does not constitute legal approval of the knowledge pack.

## Consequences

- California is the production content-authoring target for the jurisdiction extension. New York remains illustrative until separately approved.
- The decision does not change `approval_state` or `runtime_eligible`; candidate content remains fail-closed.
- California facts must use authoritative sources, carry applicability and effective-date context, and pass jurisdiction SME and legal review.
- Future jurisdiction expansion requires a separate ADR.
