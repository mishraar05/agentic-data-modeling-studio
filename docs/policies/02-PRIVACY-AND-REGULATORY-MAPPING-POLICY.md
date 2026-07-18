# Privacy and Regulatory Mapping Policy

**Policy Number**: GOV-002  
**Version**: 1.0.0  
**Effective Date**: 2025-01-XX  
**Approved By**: Chief Data Officer  
**Source**: INCREMENT_1_GOVERNANCE_REVIEW.md, Area 2, Question 2  
**Review Cycle**: Annual

---

## 1. Purpose

This policy establishes a standardized two-axis classification system for data privacy and regulatory compliance, ensuring consistent application of data protection controls, regulatory tag mapping, and label inheritance across all data assets.

---

## 2. Scope

This policy applies to:
* All data assets in the catalog
* All columns containing sensitive information
* All Unity Catalog tables and views
* All downstream derived datasets

---

## 3. Policy Statement

**Use two independent axes** for privacy classification: Sensitivity Labels (mutually exclusive, drives masking policy) and Regulatory Tags (multi-valued, applied at entity level, inherited by columns).

---

## 4. Axis 1: Sensitivity Labels

Sensitivity labels are **mutually exclusive** (one per column) and drive masking policy.

### 4.1 Sensitivity Label Definitions

| Label | Meaning | Handling | UC Controls |
|-------|---------|----------|-------------|
| **PUBLIC** | Freely disclosable | None | No restrictions |
| **INTERNAL** | Default for non-sensitive business data | RBAC only | Standard RBAC |
| **CONFIDENTIAL** | Business-sensitive (contracts, financials, pricing) | RBAC + policy. Internal policy only | RBAC + audit log |
| **PII** | Identifies a natural person | UC column mask + RLS | Column mask + row-level security |
| **SPI** | Sensitive PII — SSN/gov ID, financial account, biometric | Mask + restricted role + access audit | Column mask + restricted role + audit |
| **PHI** | Health info held by covered entity or BA | Minimum-necessary; explicit role grant; access audit | Column mask + explicit grant + audit |

### 4.2 Label Assignment Rules

1. **Default**: All new columns start as `INTERNAL` unless explicitly classified
2. **Upgrade Only**: Labels can be upgraded to stricter levels without approval (INTERNAL → PII)
3. **Downgrade Requires Approval**: Downgrading (PII → INTERNAL) requires named human approver (Steward or CDO)
4. **Column-Level Granularity**: Labels apply at column level, not table level

---

## 5. Axis 2: Regulatory Tags

Regulatory tags are **multi-valued** (multiple tags per entity), applied at entity level, and inherited by columns.

### 5.1 Supported Regulatory Tags

* **GDPR** — General Data Protection Regulation (EU)
* **UK-GDPR** — UK GDPR (post-Brexit)
* **CCPA/CPRA** — California Consumer Privacy Act / California Privacy Rights Act
* **HIPAA** — Health Insurance Portability and Accountability Act (US)
* **GLBA** — Gramm-Leach-Bliley Act (US financial institutions)
* **NAIC-668** — NAIC Model Law #668 (state insurance data security)
* **DPDP-2023** — Digital Personal Data Protection Act (India)
* **SOX** — Sarbanes-Oxley Act (US financial reporting)

### 5.2 Tag Application Rules

1. **Entity-Level**: Tags apply to tables/views
2. **Inheritance**: All columns inherit entity-level tags
3. **Multi-Value**: Entities may have multiple regulatory tags
4. **Override**: Column-level tags can override or augment entity tags

---

## 6. Default Mapping

Default sensitivity label to regulatory tag mapping (overridable per entity):

| Sensitivity Label | Default Regulatory Tags | Conditions |
|-------------------|-------------------------|------------|
| **PII** | GDPR (if EU/UK subjects), CCPA/CPRA (if CA residents), GLBA (if financial institution), DPDP (if Indian subjects) | Presence of relevant data subjects |
| **SPI** | All of the above + state breach-notification statutes | Applies to all relevant jurisdictions |
| **PHI** | HIPAA + state health laws + GDPR Art. 9 (if EU subjects) | Health data is special category under GDPR |
| **CONFIDENTIAL** | SOX (only where feeds financial reporting) | Business-sensitive, not personal data |
| **PUBLIC / INTERNAL** | None | No regulatory constraints |

---

## 7. Three Rules That Prevent Mistakes

### 7.1 PHI Outranks PII

Any HIPAA identifier in health context is **PHI**, not PII. LTC Claims defaults to PHI.

**Rationale**: HIPAA has stricter requirements than general PII regulations. Misclassifying PHI as PII creates compliance gaps.

### 7.2 GDPR's "Personal Data" Is Wider Than US "PII"

IP address, device ID, pseudonymized keys are in scope for GDPR. Hash surrogate keys derived from natural person identifiers are personal data under GDPR.

**Rationale**: GDPR's definition of personal data includes indirect identifiers. US PII standards are narrower.

### 7.3 Labels Propagate Downstream, Only Upward in Strictness

RDL → SDL → CDL inherits strictest label. Hashing does not downgrade a label unless documented de-identification method is approved.

**Rationale**: Data lineage must preserve privacy protections. Transformations don't automatically reduce sensitivity.

---

## 8. Responsibilities

### 8.1 Data Stewards
* Classify new data assets within 5 business days of onboarding
* Review and approve label downgrades
* Maintain subject geography mapping for regulatory tag application
* Document exceptions and special cases

### 8.2 Chief Data Officer
* Approve PHI classifications
* Approve label downgrades for SPI and PHI
* Review quarterly classification compliance metrics
* Approve new regulatory tag additions

### 8.3 Data Privacy Officer
* Validate regulatory tag mappings
* Review subject rights request procedures
* Approve de-identification methods for label downgrades
* Coordinate with legal on regulatory requirement changes

### 8.4 Technical Teams
* Implement Unity Catalog masking policies per sensitivity labels
* Maintain automated label propagation in lineage
* Report classification coverage gaps
* Enforce label inheritance in data pipelines

---

## 9. Compliance Monitoring

### 9.1 Metrics
* % of columns with explicit sensitivity labels
* % of entities with appropriate regulatory tags
* Label downgrade approval rate and time
* Coverage of UC masking policies for PII/SPI/PHI

### 9.2 Reporting
* Quarterly compliance report to CDO and DPO
* Monthly coverage report to stewards
* Real-time alerts for unclassified high-value assets

---

## 10. Policy Violations

Violations include:
* Unclassified sensitive data
* Incorrect label downgrades without approval
* Missing regulatory tags for in-scope data
* Bypassing masking policies

**Remediation**:
* Immediate access restriction pending classification
* Mandatory reclassification before access restoration
* Escalation to DPO for pattern violations
* Audit trail review for compliance exposure

---

## 11. Related Policies

* Data Profiling Policy (GOV-001)
* PII Detection Standards (GOV-003)
* Record Approval Workflow Policy (GOV-004)

---

## 12. Policy Review

This policy will be reviewed annually or upon:
* New privacy regulations
* Jurisdictional expansion
* Audit findings
* Technology capability changes

---

**Document Control**:
* **Created**: 2025-01-XX
* **Last Updated**: 2025-01-XX
* **Next Review**: 2026-01-XX
* **Owner**: Chief Data Officer
* **Co-Owner**: Data Privacy Officer
