# Error Handling and Override Policy

**Policy Number**: GOV-007  
**Version**: 1.0.0  
**Effective Date**: 2025-01-XX  
**Approved By**: Chief Data Officer  
**Source**: INCREMENT_1_GOVERNANCE_REVIEW.md, Area 7  
**Review Cycle**: Annual

---

## 1. Purpose

This policy establishes configurable error handling rules and validation override procedures, balancing data quality enforcement with operational flexibility. Different projects have different needs — critical projects enforce strict validation, exploratory projects work with warnings.

---

## 2. Scope

This policy applies to:
* All data validation errors
* All referential integrity violations
* All business rule violations
* All override requests and approvals
* All project-level configuration decisions

---

## 3. Policy Statement

**Strict by default, configurable per project**. Projects choose their validation enforcement level based on criticality and maturity. All overrides require documented justification and hierarchical approval.

---

## 4. Validation Enforcement Levels

### 4.1 Strict Mode (Default)

**Who Uses**: Production projects, regulatory reporting, customer-facing systems, PII/PHI-bearing domains

**Behavior**:
* All validation errors **BLOCK** operations
* No degraded modes allowed
* Hard referential integrity required
* Complete evidence chains required
* No missing required fields

**Examples of Blocked Operations**:
* Broken references (pointing to non-existent records)
* Cross-project evidence mixing
* Claims without supporting evidence
* Changes that skip required approvals
* Malformed data
* Missing privacy labels on sensitive data

### 4.2 Warning Mode

**Who Uses**: Development projects, exploratory analysis, pilot projects, early-stage work

**Behavior**:
* Validation errors generate **WARNINGS** but don't block
* Operations proceed with data quality flags
* Missing evidence marked as `INCOMPLETE`
* Incomplete data visible but flagged
* Cannot transition to production without resolving

**Examples of Allowed with Warning**:
* Partial evidence (some observations missing — marked incomplete)
* Open questions (explicitly track "still figuring this out")
* Incomplete classifications pending steward review
* Draft documentation with gaps

### 4.3 Audit Mode

**Who Uses**: Testing, sandbox environments, proof-of-concept work

**Behavior**:
* Validation errors logged but **NOT DISPLAYED**
* Operations proceed without interruption
* Validation report generated for review
* No governance gates enforced
* Cannot migrate to higher environments

**Use Case**: Understanding data quality issues before deciding on enforcement

---

## 5. What System Will Reject (All Modes)

These violations are **NEVER ALLOWED** regardless of enforcement level:

### 5.1 Structural Integrity Violations

* **Auto-approval of official records** — Always requires human approval per GOV-004
* **Sloppy/arbitrary data structures** — Schema validation always enforced
* **Changes without versioning** — Audit trail mandatory
* **Hard-deleting records** — Deprecation required per GOV-005
* **Mutating historical records** — Immutability mandatory (except break-glass per GOV-006)

### 5.2 Security and Privacy Violations

* **Unmasked PII/PHI in production** — UC masking required per GOV-002
* **Bypassing approval workflows** — Workflow integrity mandatory
* **Unauthorized label downgrades** — Approval required per GOV-002
* **Storing raw PII samples** — Prohibited per GOV-003

---

## 6. Project Configuration

### 6.1 Configuration Selection

Projects select enforcement level at creation based on:

| Project Characteristic | Recommended Level | Rationale |
|------------------------|-------------------|-----------|
| **Production, customer-facing** | Strict | Data quality impacts users directly |
| **Regulatory reporting** | Strict | Compliance requires complete, accurate data |
| **PII/PHI-bearing domains** | Strict | Privacy violations have legal consequences |
| **Development/exploratory** | Warning | Enable rapid iteration while tracking issues |
| **Proof-of-concept** | Audit | Understand data landscape before enforcement |
| **Data quality remediation** | Warning → Strict | Start permissive, tighten as quality improves |

### 6.2 Configuration Changes

| From | To | Approver | Conditions |
|------|----|-----------| -----------|
| Audit | Warning | Steward | Validation issues reviewed and documented |
| Warning | Strict | Steward → CDO | All warnings resolved or overridden with approval |
| Strict | Warning | CDO only | Temporary only, requires documented reason and timeline |
| Warning | Audit | **NOT ALLOWED** | Regression not permitted |
| Strict | Audit | **NOT ALLOWED** | Regression not permitted |

**Rationale**: Projects should tighten enforcement as they mature, never loosen without explicit CDO approval.

---

## 7. Override Authority and Procedures

### 7.1 Override Hierarchy

**Hierarchical Model**: Steward proposes override with justification → CDO approves

| Validation Type | Override Authority | Documentation Required |
|-----------------|-------------------|------------------------|
| **Referential integrity** | Steward → CDO | Business reason, risk assessment, remediation plan |
| **Missing evidence** | Steward | Explanation, timeline for completion |
| **Business rule violation** | Steward → CDO | Business justification, alternative evidence |
| **Privacy label downgrade** | Steward → CDO | Legal review, de-identification method, approval per GOV-002 |
| **Approval workflow bypass** | **NOT ALLOWED** | Cannot be overridden |

### 7.2 Override Request Process

**Step 1: Steward Proposal**
* Document validation error and context
* Provide business justification
* Assess risk and impact
* Propose remediation plan
* Set expiry date (overrides are time-limited)

**Step 2: CDO Review**
* Validate business need
* Assess governance risk
* Confirm remediation plan
* Approve or reject with reason

**Step 3: Override Execution**
* System logs override in append-only audit trail
* Override marked with approver, date, reason
* Expiry date enforced (auto-reverts if not remediated)

---

## 8. Override Governance Model

### 8.1 Override Requirements

All overrides must include:
* **Documented reason** — Why is this exception necessary?
* **Business justification** — What is the business impact?
* **Risk assessment** — What are the governance implications?
* **Remediation plan** — How and when will this be resolved?
* **Expiry date** — When does this override expire?
* **Reference to edge case** — Link to specific situation

### 8.2 Override Lifecycle

```
PROPOSED → (Steward Review) → (CDO Approval) → ACTIVE → EXPIRED or REMEDIATED
```

**ACTIVE**: Override in effect, monitoring for remediation
**EXPIRED**: Override auto-reverts, validation re-enforced
**REMEDIATED**: Root issue fixed, override no longer needed

### 8.3 Override Audit Trail

All overrides logged with:
* Override ID and timestamp
* Validation rule overridden
* Approver identity (Steward + CDO)
* Justification and reason
* Expiry date
* Remediation status
* Resolution outcome

**Audit trail is append-only** — Cannot be altered or deleted

---

## 9. Degraded Modes (Allowed in Warning Mode Only)

### 9.1 Tiered Profiling

Per Data Profiling Policy (GOV-001):
* **T1** — Always required
* **T2** — Required for PII/PHI domains
* **T3** — On request

Degraded mode: T1 only with documented reason

### 9.2 Partial Evidence

Per Data Integrity policy:
* Claims should have supporting evidence
* Degraded mode: Mark as `INCOMPLETE`, document gaps
* Timeline required for evidence completion

### 9.3 Open Questions

Per Data Integrity policy:
* Explicitly track "still figuring this out"
* Degraded mode: `UNRESOLVED` status allowed
* Cannot transition to APPROVED without resolution

---

## 10. Quarterly Override Review

### 10.1 Review Process

**Frequency**: Quarterly, mandatory

**Attendees**: CDO, Data Stewards, Data Governance Team

**Agenda**:
* Review all active overrides
* Assess remediation progress
* Identify pattern violations
* Update policies if needed

### 10.2 Pattern Analysis

**Red Flags**:
* Same validation overridden repeatedly
* Overrides requested by same steward/project repeatedly
* Overrides never remediated (always renewed)
* Overrides with vague justifications

**Actions**:
* Policy clarification or update
* Training for steward team
* System enhancement to handle edge case properly
* Escalation to CDO for structural issues

---

## 11. Responsibilities

### 11.1 Data Stewards
* Propose overrides with complete justification
* Monitor override expiry dates
* Execute remediation plans
* Report override patterns to CDO

### 11.2 Chief Data Officer
* Approve override requests
* Conduct quarterly override reviews
* Identify policy improvement opportunities
* Escalate pattern violations

### 11.3 Project Leads
* Select appropriate enforcement level for projects
* Request enforcement level changes when needed
* Ensure project team understands validation rules
* Track warning resolution progress

### 11.4 Technical Teams
* Implement configurable validation enforcement
* Maintain override audit trail
* Generate override expiry alerts
* Provide override metrics dashboard

---

## 12. Compliance Monitoring

### 12.1 Metrics

**Override Metrics**:
* Total active overrides
* Average override duration
* Override expiry compliance
* Remediation completion rate
* Pattern violations identified

**Project Enforcement Metrics**:
* Projects by enforcement level
* Enforcement level change requests
* Warning-to-strict promotion rate
* Validation error resolution time

### 12.2 Reporting

* **Weekly**: Override expiry report
* **Monthly**: Override metrics dashboard
* **Quarterly**: Pattern analysis and review
* **Annual**: Policy effectiveness assessment

---

## 13. Policy Violations

Violations include:
* Overrides without documented justification
* Bypassing override approval workflow
* Expired overrides not remediated
* Pattern violations not addressed
* Enforcement level downgrades without CDO approval

**Remediation**:
* Immediate override revocation pending proper approval
* Mandatory justification documentation
* Pattern violation investigation
* Policy training for repeat offenders

---

## 14. Edge Case Examples

### 14.1 Example 1: External Vendor Data with No Access

**Validation Error**: Cannot profile — no read access

**Override Justification**: Third-party SaaS vendor, data not accessible until migration complete

**Approved Override**:
* **Type**: Missing profiling (T1/T2/T3)
* **Approver**: Steward
* **Degraded Mode**: Publish structure-only, flagged `UNPROFILED`
* **Expiry**: 90 days or upon access grant
* **Remediation**: Profile upon data migration completion

### 14.2 Example 2: Historical Table with Missing Business Context

**Validation Error**: Dictionary entry requires business context

**Override Justification**: Table from acquired company, original business SMEs no longer available

**Approved Override**:
* **Type**: Missing business context
* **Approver**: CDO
* **Degraded Mode**: Mark context as `RECONSTRUCTED_FROM_ANALYSIS`
* **Expiry**: 180 days
* **Remediation**: Document reconstructed understanding, flag uncertainty

### 14.3 Example 3: Schema Drift During Active Development

**Validation Error**: Profiling results don't match current schema

**Override Justification**: Rapid development iteration, schema changing daily

**Approved Override**:
* **Type**: Stale profiling results
* **Approver**: Steward
* **Degraded Mode**: Warning mode, re-profile weekly
* **Expiry**: 30 days (development sprint)
* **Remediation**: Finalize schema, run T1/T2 profiling, promote to strict mode

---

## 15. Integration with Other Policies

This policy integrates with:
* **Data Profiling Policy (GOV-001)**: Defines profiling exceptions and tiers
* **Privacy & Regulatory Mapping Policy (GOV-002)**: Defines label downgrade approvals
* **PII Detection Standards (GOV-003)**: Defines detection confidence thresholds
* **Record Approval Workflow Policy (GOV-004)**: Defines approval requirements
* **Emergency Override Procedures (GOV-006)**: Defines emergency escalation paths

---

## 16. Policy Review

This policy will be reviewed annually or upon:
* Quarterly override pattern identification
* Enforcement level change trends
* Technology capability changes
* User feedback on validation friction

---

**Document Control**:
* **Created**: 2025-01-XX
* **Last Updated**: 2025-01-XX
* **Next Review**: 2026-01-XX
* **Owner**: Chief Data Officer

---

## Appendix A: Quick Reference — Enforcement Level Selection

```
CHOOSING ENFORCEMENT LEVEL FOR NEW PROJECT:

Production or customer-facing?
└─ YES → STRICT

Contains PII/PHI?
└─ YES → STRICT

Regulatory reporting?
└─ YES → STRICT

Development or exploratory?
└─ YES → WARNING (promote to STRICT when ready)

Proof-of-concept or testing?
└─ YES → AUDIT (promote to WARNING then STRICT)

Data quality remediation?
└─ YES → WARNING initially, promote to STRICT as issues resolve
```

## Appendix B: Override Request Template

```markdown
# Override Request

**Project**: [Project Name]
**Validation Rule**: [Specific rule being overridden]
**Record/Asset**: [Link to affected record]

## Business Justification
[Why is this exception necessary? What is the business impact?]

## Risk Assessment
[What are the governance implications? What could go wrong?]

## Remediation Plan
[How will this be resolved? Specific steps and timeline.]

## Expiry Date
[When should this override expire? Format: YYYY-MM-DD]

## Edge Case Reference
[Link to documentation of this specific edge case]

---

**Requested By**: [Steward Name]
**Request Date**: [YYYY-MM-DD]
**Approval Status**: [PENDING/APPROVED/REJECTED]
**Approved By**: [CDO Name, if approved]
**Approval Date**: [YYYY-MM-DD, if approved]
```
