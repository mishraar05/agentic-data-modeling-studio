# Record Approval Workflow Policy

**Policy Number**: GOV-004  
**Version**: 1.0.0  
**Effective Date**: 2025-01-XX  
**Approved By**: Chief Data Officer  
**Source**: INCREMENT_1_GOVERNANCE_REVIEW.md, Area 4, Question 1  
**Review Cycle**: Annual

---

## 1. Purpose

This policy establishes approval workflows for different record types, ensuring appropriate governance oversight for official publications while enabling efficient project work. Clear approval chains prevent incomplete or incorrect definitions from becoming authoritative.

---

## 2. Scope

This policy applies to:
* All official records (published definitions, final deliverables)
* All working records (project status, tasks)
* All historical records (observations, profiling runs, audit logs)
* All lifecycle state transitions

---

## 3. Policy Statement

**Different rules for different record types**: Official records require hierarchical human approval (Steward → CDO). Working records enable team self-service. Historical records are immutable.

---

## 4. Record Type Definitions

### 4.1 Working Records

**Definition**: Project status, tasks, internal notes, draft work products

**Characteristics**:
* Support ongoing project work
* Not authoritative outside project context
* Frequently updated during project lifecycle
* Not subject to external compliance requirements

**Examples**:
* Project task status
* Internal meeting notes
* Draft analysis
* Work-in-progress documentation

**Lifecycle States**: `DRAFT` → `ACTIVE` → `COMPLETE` / `CANCELLED`

**Approval Required**: **NO** — Project team updates status freely

### 4.2 Official Records

**Definition**: Published definitions, approved deliverables, authoritative documentation

**Characteristics**:
* Become part of organizational knowledge base
* Referenced by downstream systems and users
* Subject to compliance and audit requirements
* Require explicit human approval before publication

**Examples**:
* Business glossary terms
* Published data dictionary entries
* Certified table documentation
* Approved semantic models

**Lifecycle States**: `DRAFT` → `PROPOSED` → `APPROVED` → `DEPRECATED` → `RETIRED`

**Approval Required**: **YES** — Hierarchical approval (Steward → CDO)

### 4.3 Historical Records

**Definition**: Immutable observations, facts, audit events, profiling results

**Characteristics**:
* Capture point-in-time truth
* Never modified after creation
* Corrections via new records, not edits
* Critical for compliance and audit trails

**Examples**:
* Data profiling results
* PII detection findings
* Schema snapshots
* Approval audit logs

**Lifecycle States**: `CREATED` (terminal state)

**Approval Required**: **NO** — Auto-created by system

**Modifications Allowed**: **NONE** — Corrections create new records

---

## 5. Hierarchical Approval Model

### 5.1 Approval Chain

**Standard Chain**: Steward Review → CDO Approval

```
DRAFT → (Steward Review) → PROPOSED → (CDO Approval) → APPROVED
```

### 5.2 Roles and Responsibilities

#### Data Steward
* **Proposes** official records for approval
* **Reviews** draft content for completeness and accuracy
* **Validates** supporting evidence and documentation
* **Recommends** approval or rejection with justification

#### Chief Data Officer (CDO)
* **Approves** official records for publication
* **Ensures** governance policy compliance
* **Validates** business impact and stakeholder alignment
* **Authorizes** publication to catalog

### 5.3 Service Level Agreements

| Transition | Responsible Party | SLA | Escalation |
|------------|-------------------|-----|------------|
| DRAFT → PROPOSED | Steward | 3 business days | Steward manager |
| PROPOSED → APPROVED | CDO | 2 business days | CDO (no escalation) |
| Total (DRAFT → APPROVED) | — | 5 business days | — |

### 5.4 Rejection Handling

Either steward or CDO may reject at their stage:
* **Rejection requires**: Written reason and specific remediation guidance
* **Rejected record returns to**: `DRAFT` state
* **Submitter notified**: Within 4 hours of rejection
* **Remediation tracking**: Rejection reason captured in audit log

---

## 6. State Transition Rules

### 6.1 Working Records

| From State | To State | Who Can Transition | Approval Required | Conditions |
|------------|----------|-------------------|-------------------|------------|
| DRAFT | ACTIVE | Project team | No | Ready to begin work |
| ACTIVE | COMPLETE | Project team | No | Work finished successfully |
| ACTIVE | CANCELLED | Project team | No | Work abandoned or deprioritized |
| COMPLETE | ACTIVE | Project team | No | Rework needed |

### 6.2 Official Records

| From State | To State | Who Can Transition | Approval Required | Conditions |
|------------|----------|-------------------|-------------------|------------|
| DRAFT | PROPOSED | Steward | Steward review | Complete, evidence-backed, ready for publication |
| PROPOSED | APPROVED | CDO | CDO approval | Governance compliant, business aligned |
| PROPOSED | DRAFT | Steward or CDO | Rejection | Incomplete or non-compliant, remediation needed |
| APPROVED | DEPRECATED | Steward or CDO | See Deprecation Policy (GOV-005) | Asset retired, definition superseded |
| DEPRECATED | RETIRED | System | Automatic | 12 months in DEPRECATED state |
| APPROVED | APPROVED | CDO | Re-approval | Material changes to approved record |

### 6.3 Historical Records

| From State | To State | Who Can Transition | Approval Required | Conditions |
|------------|----------|-------------------|-------------------|------------|
| (none) | CREATED | System | Automatic | Observation recorded |

**No other transitions allowed** — Historical records are immutable

---

## 7. Approval Workflow Enforcement

### 7.1 Technical Controls

1. **State Machine Enforcement**: Database constraints prevent invalid state transitions
2. **Approval Audit Trail**: All approvals logged with approver identity, timestamp, and reason
3. **Role-Based Permissions**: Only authorized roles can transition to approval states
4. **Publication Gate**: `APPROVED` state required before publication to catalog

### 7.2 Process Controls

1. **Review Checklist**: Stewards complete mandatory checklist before PROPOSED transition
2. **Supporting Evidence**: All official records link to supporting observations/analysis
3. **Completeness Check**: System validates required fields before PROPOSED transition
4. **Notification**: Automated notifications to approvers upon state transitions

---

## 8. Review Checklist for Stewards

Before transitioning DRAFT → PROPOSED, steward must verify:

- [ ] All required fields completed
- [ ] Supporting evidence linked and accessible
- [ ] Privacy labels assigned and validated
- [ ] Regulatory tags applied per GOV-002
- [ ] Profiling completed per GOV-001 (if applicable)
- [ ] PII detection reviewed per GOV-003 (if applicable)
- [ ] Business glossary terms aligned
- [ ] Stakeholder feedback incorporated
- [ ] Version history documented
- [ ] Related records cross-referenced

---

## 9. Responsibilities

### 9.1 Data Stewards
* Review draft official records for completeness
* Complete review checklist before proposing
* Provide clear rejection reasons when applicable
* Meet 3-day review SLA
* Track remediation of rejected records

### 9.2 Chief Data Officer
* Approve official records for publication
* Ensure governance policy compliance
* Provide clear rejection reasons when applicable
* Meet 2-day approval SLA
* Review approval metrics quarterly

### 9.3 Project Teams
* Maintain working records for project tracking
* Transition working records appropriately
* Prepare official records for steward review
* Respond to rejection feedback

### 9.4 Technical Teams
* Maintain state machine enforcement
* Implement approval workflow automation
* Generate approval audit reports
* Alert on SLA violations

---

## 10. Compliance Monitoring

### 10.1 Metrics
* Approval turnaround time by approver
* Rejection rate and reasons
* SLA compliance rate
* % of official records with complete approval trail
* Average time in PROPOSED state

### 10.2 Reporting
* Weekly SLA compliance report
* Monthly approval metrics to CDO
* Quarterly rejection pattern analysis
* Annual workflow effectiveness review

---

## 11. Policy Violations

Violations include:
* Publishing official records without approval
* Bypassing approval workflow
* Missing approval audit trail
* Exceeding SLA without escalation

**Remediation**:
* Immediate unpublishing of non-compliant records
* Retroactive approval required for republication
* Workflow audit and control remediation
* Escalation to CDO for pattern violations

---

## 12. Integration with Other Policies

This policy integrates with:
* **Data Profiling Policy (GOV-001)**: Profiling completion required before PROPOSED
* **Privacy & Regulatory Mapping Policy (GOV-002)**: Classification required before PROPOSED
* **PII Detection Standards (GOV-003)**: PII review required before PROPOSED
* **Record Deprecation Policy (GOV-005)**: Defines DEPRECATED and RETIRED transitions
* **Emergency Override Procedures (GOV-006)**: Defines emergency escalation paths

---

## 13. Policy Review

This policy will be reviewed annually or upon:
* Workflow bottleneck identification
* SLA violation trends
* Regulatory requirement changes
* Organizational structure changes

---

**Document Control**:
* **Created**: 2025-01-XX
* **Last Updated**: 2025-01-XX
* **Next Review**: 2026-01-XX
* **Owner**: Chief Data Officer
