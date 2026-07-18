# Data Governance Policies

**Status**: ✅ **APPROVED FOR PRODUCTION**  
**Source**: INCREMENT_1_GOVERNANCE_REVIEW.md  
**Effective Date**: 2025-01-XX  
**Approved By**: Chief Data Officer  
**Version**: 1.0.0

---

## Overview

This directory contains the formal data governance policies for the Agentic Data Modeling Studio. These policies were derived from comprehensive human governance review (Increment 1) and establish the operational rules for data profiling, privacy classification, PII detection, approval workflows, record lifecycle, emergency procedures, and error handling.

**All policies are production-approved and enforceable immediately upon effective date.**

---

## Policy Index

### GOV-001: Data Profiling Policy
**File**: [01-DATA-PROFILING-POLICY.md](01-DATA-PROFILING-POLICY.md)  
**Purpose**: Mandatory data profiling requirements with tiered depth (T1/T2/T3) and narrow exception path  
**Key Topics**:
* Tiered profiling depth (Structural, Statistical, Relational)
* Exception categories and approval requirements
* Hard gate for publication (no profiling = no publication)
* Compliance monitoring and violation remediation

**When to Reference**: Before onboarding new data assets, during profiling runs, when requesting profiling exceptions

---

### GOV-002: Privacy and Regulatory Mapping Policy
**File**: [02-PRIVACY-AND-REGULATORY-MAPPING-POLICY.md](02-PRIVACY-AND-REGULATORY-MAPPING-POLICY.md)  
**Purpose**: Two-axis classification system (Sensitivity Labels + Regulatory Tags) for consistent privacy controls  
**Key Topics**:
* Sensitivity label definitions (PUBLIC, INTERNAL, CONFIDENTIAL, PII, SPI, PHI)
* Regulatory tag mapping (GDPR, CCPA, HIPAA, etc.)
* Three rules that prevent mistakes (PHI outranks PII, GDPR wider than US PII, downstream propagation)
* Label assignment and downgrade approval requirements

**When to Reference**: When classifying data assets, assigning privacy labels, mapping to regulations, downgrading labels

---

### GOV-003: PII Detection Standards
**File**: [03-PII-DETECTION-STANDARDS.md](03-PII-DETECTION-STANDARDS.md)  
**Purpose**: Accuracy targets and operating rules for automated PII detection (high recall ≥98-99%)  
**Key Topics**:
* Asymmetric cost model (false negatives >> false positives)
* Tiered targets by type (Deterministic, Probabilistic, Free text)
* Three-state output (CONFIRMED, CANDIDATE, NOT_DETECTED)
* Gold set maintenance and performance tracking
* Incident response for false negative discoveries

**When to Reference**: When running PII detection, reviewing CANDIDATE detections, investigating false negatives, updating detection methods

---

### GOV-004: Record Approval Workflow Policy
**File**: [04-RECORD-APPROVAL-WORKFLOW-POLICY.md](04-RECORD-APPROVAL-WORKFLOW-POLICY.md)  
**Purpose**: Hierarchical approval workflows (Steward → CDO) for different record types  
**Key Topics**:
* Record type definitions (Working, Official, Historical)
* Approval chain and SLAs (5 business days total)
* State transition rules and enforcement
* Review checklist for stewards
* Rejection handling and remediation

**When to Reference**: When proposing official records for approval, reviewing draft records, handling rejections, monitoring SLA compliance

---

### GOV-005: Record Deprecation and Lifecycle Policy
**File**: [05-RECORD-DEPRECATION-AND-LIFECYCLE-POLICY.md](05-RECORD-DEPRECATION-AND-LIFECYCLE-POLICY.md)  
**Purpose**: Lifecycle rules for deprecation, retirement, and supersession (never hard-delete)  
**Key Topics**:
* Record type distinctions (Definition, Observation, Deliverable)
* Status ladder (DRAFT → PROPOSED → APPROVED → DEPRECATED → RETIRED)
* Asymmetric approval (deprecate deliverable = Steward only, deprecate definition = CDO)
* Event-driven and time-based triggers
* REVIEW_DUE flag and attestation procedures

**When to Reference**: When deprecating records, superseding definitions, managing review cycles, handling asset decommissioning

---

### GOV-006: Emergency Override Procedures
**File**: [06-EMERGENCY-OVERRIDE-PROCEDURES.md](06-EMERGENCY-OVERRIDE-PROCEDURES.md)  
**Purpose**: Emergency correction procedures (additive-only universal + narrow dual-control break-glass)  
**Key Topics**:
* Additive-only corrections for historical records
* CONTESTED flag mechanism (instant, no approval)
* Dual control break-glass for PII/PHI redaction
* Anti-abuse controls (make it loud, not hard)
* Design prevention (never store raw sample values)

**When to Reference**: When correcting historical records, handling urgent definition errors, redacting PII/PHI exposure, investigating override patterns

---

### GOV-007: Error Handling and Override Policy
**File**: [07-ERROR-HANDLING-AND-OVERRIDE-POLICY.md](07-ERROR-HANDLING-AND-OVERRIDE-POLICY.md)  
**Purpose**: Configurable validation enforcement per project (Strict/Warning/Audit) with override procedures  
**Key Topics**:
* Three enforcement levels and selection criteria
* What system always rejects (structural, security, privacy violations)
* Override hierarchy (Steward → CDO) and governance model
* Degraded modes (allowed in Warning mode only)
* Quarterly override review and pattern analysis

**When to Reference**: When selecting enforcement level, requesting validation overrides, conducting quarterly reviews, handling edge cases

---

## Policy Relationships

### Policy Dependencies

```
GOV-001 (Profiling) ←─────┐
                          │
GOV-002 (Privacy) ←───────┼──→ GOV-004 (Approval)
                          │        ↓
GOV-003 (PII Detection) ←─┤   GOV-005 (Lifecycle)
                          │        ↓
                          └──→ GOV-006 (Emergency)
                                   ↓
                              GOV-007 (Overrides)
```

* **GOV-004** (Approval) gates publication for all record types
* **GOV-001**, **GOV-002**, **GOV-003** define pre-approval requirements
* **GOV-005** (Lifecycle) defines post-approval lifecycle management
* **GOV-006** (Emergency) provides escape valves for urgent situations
* **GOV-007** (Overrides) provides flexibility for edge cases

---

## Common Workflows

### Workflow 1: Onboarding New Data Asset

1. **Profile data** per GOV-001 (T1/T2/T3 based on domain)
2. **Classify privacy** per GOV-002 (assign labels and tags)
3. **Detect PII** per GOV-003 (review CANDIDATE findings)
4. **Prepare documentation** (complete steward checklist)
5. **Submit for approval** per GOV-004 (Steward → CDO)
6. **Publish upon approval** (hard gate enforced)

### Workflow 2: Correcting Approved Definition

**Non-Urgent (Normal)**:
1. Create superseding version (DRAFT)
2. Submit for approval per GOV-004
3. Upon approval, old version → SUPERSEDED per GOV-005

**Urgent (Production Incident)**:
1. Apply CONTESTED flag per GOV-006 (instant)
2. Readers see correction immediately
3. Submit superseding version within 48h
4. Normal approval chain follows

### Workflow 3: Handling PII Detection False Negative

1. **Immediate** (minutes): Mask column per GOV-002 (data plane)
2. **Within 4h**: Notify CDO + DPO per GOV-003
3. **Within 24h**: Root cause analysis, update gold set
4. **Within 48h**: Re-scan similar assets, deploy fix
5. **Within 1 week**: Incident review, method improvement

### Workflow 4: Requesting Validation Override

1. **Document justification** per GOV-007 (business need, risk, remediation)
2. **Submit to Steward** for review
3. **Steward proposes to CDO** with assessment
4. **CDO approves** with expiry date
5. **Monitor remediation** progress
6. **Quarterly review** of override patterns

---

## Governance Roles

### Data Stewards
* Review and propose official records (GOV-004)
* Execute profiling and classification (GOV-001, GOV-002)
* Review PII detection findings (GOV-003)
* Manage record lifecycle (GOV-005)
* Apply CONTESTED flags (GOV-006)
* Request validation overrides (GOV-007)

### Chief Data Officer (CDO)
* Approve official records (GOV-004)
* Approve definition deprecations (GOV-005)
* Approve validation overrides (GOV-007)
* Ratify break-glass redactions (GOV-006)
* Review quarterly governance metrics (all policies)

### Data Privacy Officer (DPO)
* Validate regulatory tag mappings (GOV-002)
* Review PII detection performance (GOV-003)
* Co-ratify break-glass redactions (GOV-006)
* Assess breach notification requirements (GOV-003, GOV-006)

### Technical Teams
* Execute profiling runs (GOV-001)
* Implement masking policies (GOV-002)
* Maintain detection algorithms (GOV-003)
* Enforce approval workflows (GOV-004)
* Automate lifecycle transitions (GOV-005)
* Implement override controls (GOV-007)

---

## Compliance Monitoring

### Key Metrics (Across All Policies)

* **Profiling Coverage**: % of published assets with valid profiling (GOV-001)
* **Classification Coverage**: % of columns with explicit sensitivity labels (GOV-002)
* **PII Detection Performance**: Recall/precision by tier (GOV-003)
* **Approval SLA Compliance**: % of approvals within 5-day SLA (GOV-004)
* **Lifecycle Compliance**: % of records with overdue attestations (GOV-005)
* **Override Volume**: Break-glass invocations per year (GOV-006)
* **Override Remediation**: % of overrides remediated before expiry (GOV-007)

### Reporting Cadence

* **Real-time**: Break-glass invocations, false negative discoveries
* **Weekly**: SLA compliance, override expiry
* **Monthly**: Coverage metrics, steward workload
* **Quarterly**: Pattern analysis, policy effectiveness, override review
* **Annual**: Policy review, gold set refresh

---

## Policy Review Schedule

| Policy | Review Frequency | Next Review | Trigger Events |
|--------|------------------|-------------|----------------|
| GOV-001 | Annual | 2026-01-XX | Regulatory changes, tech capabilities |
| GOV-002 | Annual | 2026-01-XX | New regulations, jurisdictional expansion |
| GOV-003 | Annual | 2026-01-XX | False negative incidents, detection updates |
| GOV-004 | Annual | 2026-01-XX | Workflow bottlenecks, SLA violations |
| GOV-005 | Annual | 2026-01-XX | Regulatory retention changes, audit findings |
| GOV-006 | Annual | 2026-01-XX | Break-glass invocation, pattern violations |
| GOV-007 | Annual | 2026-01-XX | Override pattern trends, user feedback |

---

## Document Control

* **Policy Suite Version**: 1.0.0
* **Total Policies**: 7
* **Status**: Production-Approved
* **Approval Authority**: Chief Data Officer
* **Approval Date**: 2025-01-XX
* **Effective Date**: 2025-01-XX
* **Source Document**: `contracts/INCREMENT_1_GOVERNANCE_REVIEW.md`

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-XX | Genie Code | Initial policy suite created from Increment 1 governance review |

---

## Questions or Issues?

For policy clarification, interpretation questions, or proposed amendments:
* **Operational Questions**: Contact your Data Steward
* **Policy Interpretation**: Contact Chief Data Officer
* **Privacy Questions**: Contact Data Privacy Officer
* **Technical Implementation**: Contact Data Governance Technical Lead

---

**This policy suite represents the foundational governance framework for the Agentic Data Modeling Studio. All future increments and enhancements must comply with these policies unless explicitly amended through the formal policy review process.**
