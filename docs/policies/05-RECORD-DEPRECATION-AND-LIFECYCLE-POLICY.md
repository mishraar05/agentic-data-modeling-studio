# Record Deprecation and Lifecycle Policy

**Policy Number**: GOV-005  
**Version**: 1.0.0  
**Effective Date**: 2025-01-XX  
**Approved By**: Chief Data Officer  
**Source**: INCREMENT_1_GOVERNANCE_REVIEW.md, Area 4, Question 2  
**Review Cycle**: Annual

---

## 1. Purpose

This policy establishes lifecycle rules for different record types, defining when and how records are deprecated, retired, or superseded. The policy ensures records remain resolvable for audit and regulatory purposes while managing visibility and freshness.

---

## 2. Scope

This policy applies to:
* All official records (definitions, deliverables)
* All historical records (observations)
* All deprecation and retirement workflows
* All attestation and review cycles

---

## 3. Core Principle

**Never Hard-Delete**: Records stay resolvable by permalink forever for audit, regulatory defense, and lineage. Deprecation controls visibility, not existence.

---

## 4. Record Type Distinctions

Different record types have different lifecycles based on what they assert:

| Record Type | What It Asserts | Lifecycle | Deprecation Trigger |
|-------------|-----------------|-----------|---------------------|
| **Definition** | "This concept means X" | Bound to concept, not asset. Outlives the table | Business concept retired |
| **Observation** | "At timestamp T, this was true" | Never deprecates — expires. Permanent point-in-time truth | N/A — Goes stale, not wrong |
| **Deliverable** | "This asset works like this" | Bound to asset. Dies with asset | Asset decommissioned |

---

## 5. Status Ladder

### 5.1 Primary States

```
DRAFT → PROPOSED → APPROVED → DEPRECATED → RETIRED
```

### 5.2 Additional States and Flags

* **SUPERSEDED** (terminal state, points at successor version)
* **REVIEW_DUE** (flag, not status — can be APPROVED and REVIEW_DUE simultaneously)
* **CONTESTED** (flag for immediate correction visibility — see Emergency Override Procedures, GOV-006)

---

## 6. DEPRECATED State

### 6.1 What DEPRECATED Means

* Hidden from default search; findable with explicit filter
* Banner: "Deprecated [date]. [reason]. See [successor link]."
* Excluded from freshness/coverage metrics
* Still returned in lineage queries
* Still resolvable by permalink
* Still included in audit trails

### 6.2 RETIRED State

* Auto-transition after **12 months in DEPRECATED** state
* Blocked while downstream dependencies remain
* Even more restricted visibility (admin/audit only)
* Still resolvable by permalink
* Permanent archival state

---

## 7. Approval Symmetry — Deliberately Asymmetric

| Action | Approver | Why |
|--------|----------|-----|
| **Supersede** (meaning changed → new version) | Full chain: Steward → CDO | Asserting new truth, same bar as creation |
| **Deprecate deliverable** (asset gone, meaning unchanged) | Steward only, no CDO | Recording verified fact (table dropped), not asserting |
| **Retire** (drop from default view) | Automatic, no approval | Purely visibility change |
| **Un-deprecate** | Full chain: Steward → CDO | Resurrection is an assertion |
| **Deprecate definition** (concept retired) | Full chain: Steward → CDO | Business decision that concept is dead |

**Rationale**: Recording facts requires less governance than asserting new truth. Deprecating a deliverable when the table is gone is documentation, not decision-making.

---

## 8. Deprecation Triggers

### 8.1 Event-Driven (Primary, Automatic)

| Event | Action | Record Type | Approval |
|-------|--------|-------------|----------|
| **Asset decommissioned / table dropped** | Deliverable auto-DEPRECATED | Deliverable | System automatic |
| **Schema drift on documented column** | Deliverable flagged REVIEW_DUE | Deliverable | None (flag only) |
| **Source system retired** | All deliverables for that source auto-DEPRECATED | Deliverable | System automatic |
| **Source system retired** | All definitions queued for re-binding | Definition | Manual (Steward → CDO) |
| **Business rule change** | Steward files superseding version | Definition | Steward → CDO |

### 8.2 Time-Based (Safety Net, Tiered)

| Record Type | Review Frequency | Action Type | Conditions |
|-------------|------------------|-------------|------------|
| **Regulated / PII-PHI-bearing definitions** | Annual | Attestation | Mandatory |
| **Other definitions** | Biennial, or on-touch | Attestation | Any edit resets clock |
| **Observations** | No review | Auto-stale | Show age after profiling cadence window |
| **Deliverables** | Inherit asset review cycle | Inherit | No independent clock |

**Attestation vs Re-Approval**: One steward click confirming "still accurate" with reason field. Only changes enter approval chain.

---

## 9. Worked Example: Customer Table Decommissioned in 2026

### 9.1 Table Documentation (Deliverable)
* **Action**: Auto-DEPRECATED on decommission event
* **Banner**: "Deprecated 2026-05-15. Customer table decommissioned. See [customer_v2](#link)."
* **Status**: Stays resolvable by permalink
* **Visibility**: Hidden from default search

### 9.2 2024 Profiling Results (Observations)
* **Action**: Untouched
* **Rationale**: They were true in 2024 and still are
* **Display**: Timestamped, self-describe as historical
* **Status**: Permanent, never deprecated

### 9.3 "Customer" Glossary Term (Definition)
* **Action**: Untouched and re-bound, not deprecated
* **Rationale**: Concept still exists
* **New Binding**: Flows to new system's `customer_v2` table
* **Deprecation**: Only if concept is retired (requires CDO approval)

---

## 10. SUPERSEDED Workflow

### 10.1 When to Supersede

Use SUPERSEDED when:
* Definition meaning changed substantially
* Business rule interpretation changed
* Regulatory interpretation changed
* Material error discovered in approved definition

Do NOT use SUPERSEDED when:
* Minor wording improvements (amendment, not supersession)
* Formatting changes
* Typo corrections

### 10.2 Supersession Process

1. **Create new version**: Steward drafts new definition in DRAFT state
2. **Link to predecessor**: New version explicitly references superseded version
3. **Full approval chain**: New version goes through Steward → CDO
4. **Upon approval of new version**: Old version auto-transitions to SUPERSEDED
5. **Banner on old version**: "Superseded by [new version link] on [date]. Reason: [brief]."
6. **Permalink preservation**: Old version remains resolvable

---

## 11. REVIEW_DUE Flag

### 11.1 When REVIEW_DUE Is Set

* Time-based attestation window expires
* Schema drift detected on documented columns
* Upstream dependency deprecated
* Regulatory requirement change impacts asset
* Manual flag by steward or CDO

### 11.2 REVIEW_DUE Handling

* Record remains APPROVED (status unchanged)
* Visual indicator in UI (yellow banner)
* Steward assigned review task
* 30-day SLA to complete attestation
* Overdue flags escalate to CDO

### 11.3 Review Actions

* **Attestation**: "Still accurate, no changes" → Clear REVIEW_DUE flag
* **Amendment**: Minor changes, stays APPROVED → Clear REVIEW_DUE flag
* **Supersession**: Material changes → Create new version, old → SUPERSEDED

---

## 12. Downstream Dependency Blocking

### 12.1 Retirement Blocking Rule

A record **cannot transition to RETIRED** while downstream dependencies exist:
* Views referencing the table
* Pipelines consuming the data
* Dashboards querying the table
* Documented mappings to the asset

### 12.2 Dependency Resolution

Before retiring:
1. **Identify dependencies**: System generates dependency report
2. **Notify stakeholders**: Automated notifications to dependency owners
3. **Grace period**: 90 days to migrate or acknowledge
4. **Force retirement**: CDO can override block after grace period with documented reason

---

## 13. Responsibilities

### 13.1 Data Stewards
* Execute time-based attestations within SLA
* Propose superseding versions when needed
* Respond to REVIEW_DUE flags within 30 days
* Document deprecation reasons clearly
* Manage deliverable deprecation for asset changes

### 13.2 Chief Data Officer
* Approve definition supersessions and deprecations
* Override retirement blocks when necessary
* Review quarterly lifecycle metrics
* Approve grace period extensions

### 13.3 Technical Teams
* Implement event-driven deprecation automation
* Maintain dependency tracking
* Generate REVIEW_DUE alerts
* Execute automatic DEPRECATED → RETIRED transitions
* Preserve permalink resolution

---

## 14. Compliance Monitoring

### 14.1 Metrics
* % of records with overdue attestations
* Average time in DEPRECATED state
* Retirement blocking incidents
* Supersession approval turnaround time
* Stale observation age distribution

### 14.2 Reporting
* Monthly REVIEW_DUE aging report
* Quarterly lifecycle transition report
* Annual attestation compliance report
* Ad-hoc dependency impact analysis

---

## 15. Policy Violations

Violations include:
* Hard-deleting records instead of deprecating
* Deprecating definitions without CDO approval
* Ignoring REVIEW_DUE flags beyond SLA
* Bypassing retirement dependency blocks

**Remediation**:
* Immediate restoration of deleted records from backup
* Escalation to CDO for approval gaps
* Mandatory attestation completion
* Dependency resolution before retry

---

## 16. Integration with Other Policies

This policy integrates with:
* **Record Approval Workflow Policy (GOV-004)**: Defines approval chains for supersession
* **Data Profiling Policy (GOV-001)**: Defines observation expiry (stale profiling)
* **Emergency Override Procedures (GOV-006)**: Defines CONTESTED flag usage
* **Privacy & Regulatory Mapping Policy (GOV-002)**: Defines regulated definition review frequency

---

## 17. Policy Review

This policy will be reviewed annually or upon:
* Regulatory retention requirement changes
* Audit findings on record lifecycle
* Technology capability changes
* Organizational knowledge management changes

---

**Document Control**:
* **Created**: 2025-01-XX
* **Last Updated**: 2025-01-XX
* **Next Review**: 2026-01-XX
* **Owner**: Chief Data Officer
