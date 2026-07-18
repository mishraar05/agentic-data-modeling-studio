# PII Detection Standards

**Policy Number**: GOV-003  
**Version**: 1.0.0  
**Effective Date**: 2025-01-XX  
**Approved By**: Chief Data Officer  
**Source**: INCREMENT_1_GOVERNANCE_REVIEW.md, Area 2, Question 3  
**Review Cycle**: Annual

---

## 1. Purpose

This policy establishes accuracy targets, operating rules, and quality assurance procedures for automated PII detection, ensuring high recall to prevent data breaches while maintaining acceptable precision to avoid operational friction.

---

## 2. Scope

This policy applies to:
* All automated PII detection processes
* All data profiling runs (T1, T2, T3)
* All new columns and schema changes
* All detection method updates and model changes

---

## 3. Policy Statement

**High recall (≥98-99%), acceptable precision (70-85%)**

PII detection optimizes for **preventing false negatives** (missed PII) over avoiding false positives (over-flagging), reflecting the asymmetric cost model where undetected PII creates regulatory exposure while false positives create manageable review work.

---

## 4. Asymmetric Cost Model

### 4.1 Cost of False Negative (Missed PII)
* Unmasked SSN/PHI in queryable production table
* Notifiable data breach
* Regulatory fines and exposure
* Emergency remediation project
* Reputational damage

### 4.2 Cost of False Positive (Over-Flagged)
* Data steward spends 5 minutes clearing flag
* Column temporarily over-masked
* Minimal business impact
* Easily corrected

**Conclusion**: False negatives are 100x-1000x more costly than false positives. Detection must prioritize recall.

---

## 5. Tiered Targets by Type

| Tier | PII Types | Recall Target | Precision Target | Action |
|------|-----------|---------------|------------------|--------|
| **A — Deterministic** | SSN, credit card (Luhn), NPI, gov ID, formatted policy/claim numbers | ≥99% | ≥95% | Auto-apply mask |
| **B — Probabilistic** | Name, address, email, phone, DOB | ≥98% | 70-85% | Auto-flag, mask-pending, steward confirms |
| **C — Free text / Quasi-identifier** | Claim notes, adjuster comments, care assessments | No detection target | N/A | Restricted by default |

### 5.1 Tier A — Deterministic

**Characteristics**:
* Well-defined format patterns
* Strong validation algorithms (Luhn checksum, format masks)
* Column name + value pattern provides high confidence

**Examples**:
* SSN: `###-##-####` or `#########` with checksum validation
* Credit card: Luhn algorithm validation + BIN ranges
* NPI: 10 digits with Luhn checksum

**Action**: Auto-apply sensitivity label and UC mask immediately

### 5.2 Tier B — Probabilistic

**Characteristics**:
* Varied formats or free-form values
* Requires ML or NLP techniques
* Column name + sample values provide moderate confidence

**Examples**:
* Name: "John Smith", "Smith, John", "SMITH JOHN"
* Address: Varied formats, international variations
* Email: format validation + domain checks
* Phone: Multiple formats, country variations

**Action**: Auto-flag as CANDIDATE, apply mask pending steward review (5 business day SLA)

### 5.3 Tier C — Free Text

**Characteristics**:
* Unstructured narrative
* PII embedded in context
* High false positive rate for extraction

**Examples**:
* Claim notes: "Claimant John Smith stated that..."
* Medical assessments: Free-form clinical narratives
* Adjuster comments: Investigative notes

**Action**: Restricted access by default, no automated detection attempted

---

## 6. Operating Rules

### 6.1 Automation is Additive-Only

Detection can propose **adding** a label. It can **never remove or downgrade** one. Downgrade always requires named human approver per Privacy & Regulatory Mapping Policy (GOV-002).

**Rationale**: Prevents automated de-escalation of actual PII. Human judgment required for downgrade decisions.

### 6.2 Three-State Output with Fail-Safe Default

All detection outputs one of three states:

| State | Meaning | Masking | Review Required |
|-------|---------|---------|-----------------|
| **CONFIRMED** | High confidence PII detected | Mask auto-applied | No (Tier A only) |
| **CANDIDATE** | Probable PII, pending confirmation | Masked while pending | Yes (5 business day SLA) |
| **NOT_DETECTED** | No PII indicators found | No mask | Periodic re-scan |

**Fail-Safe Default**: New columns start **unclassified = restricted** until scanned.

### 6.3 New Columns = Unclassified = Restricted Until Scanned

Schema drift detection must trigger immediate PII scan. Unscanned columns are:
* Flagged as `UNCLASSIFIED`
* Access restricted to steward roles only
* Auto-queued for next profiling run
* Cannot be promoted to production tables

**Integration**: Wire to schema drift detection and change data capture.

### 6.4 Human Review Required For

* Any label downgrade (CANDIDATE → NOT_PII, PII → INTERNAL)
* All Tier B detections
* All Tier C detections
* Everything in LTC Claims domain regardless of tier
* Any detection uncertainty score below 0.85

### 6.5 Human Review NOT Required For

* Tier A with checksum validation + column-name context match
* Re-confirmation of previously reviewed CONFIRMED labels
* Periodic re-scans of stable schemas (no human action needed)

### 6.6 Measure It — Gold Set and Performance Tracking

**Gold Set Maintenance**:
* Maintain hand-labelled gold set: **200-500 columns**
* Represent all Tier A and B types
* Include edge cases and false positive examples
* Update quarterly or upon detection method changes

**Performance Reporting**:
* Report recall/precision per PII type each release
* Track false negative incidents in production
* Any FN found in production is an **incident** (root cause analysis required)

---

## 7. Detection Method Transparency

### 7.1 Method Registry

All detection methods must be registered with:
* Method name and version
* Algorithm type (regex, ML model, NLP, hybrid)
* Training data source and date
* Tier A/B/C applicability
* Known limitations and edge cases

### 7.2 Model Changes

Any detection model or algorithm change must:
* Run against gold set before deployment
* Meet or exceed previous recall targets
* Document any precision tradeoffs
* Notify stewards of method changes

---

## 8. Responsibilities

### 8.1 Data Stewards
* Review CANDIDATE detections within 5 business day SLA
* Confirm or reject automated PII classifications
* Report false negatives immediately
* Contribute to gold set expansion

### 8.2 Chief Data Officer
* Approve detection method changes
* Review quarterly performance metrics
* Approve recall/precision target adjustments
* Escalate false negative incidents

### 8.3 Data Science / ML Teams
* Maintain and improve detection algorithms
* Achieve recall/precision targets per tier
* Report performance against gold set
* Investigate false negative root causes

### 8.4 Technical Teams
* Execute automated detection in profiling pipelines
* Implement fail-safe defaults for new columns
* Wire schema drift detection to PII scans
* Maintain detection method registry

---

## 9. Compliance Monitoring

### 9.1 Metrics
* Recall and precision by tier and PII type
* Detection coverage (% of columns scanned)
* Steward review turnaround time for CANDIDATEs
* False negative incident count (target: 0)
* Gold set coverage and freshness

### 9.2 Reporting
* Quarterly performance report to CDO
* Monthly steward review backlog report
* Real-time alerts for false negative discoveries
* Annual gold set refresh and re-validation

---

## 10. Policy Violations

Violations include:
* Deploying detection methods that miss recall targets
* Bypassing fail-safe defaults for new columns
* Downgrading labels without human approval
* False negative incidents without root cause analysis

**Remediation**:
* Immediate rollback of underperforming detection methods
* Emergency re-scan of affected assets
* Mandatory root cause analysis for false negatives
* Enhanced gold set with missed patterns

---

## 11. Incident Response

### 11.1 False Negative Discovery

When undetected PII is discovered in production:
1. **Immediate**: Apply mask, restrict access, create incident ticket
2. **Within 4 hours**: Notify CDO, DPO, and security team
3. **Within 24 hours**: Root cause analysis, update gold set
4. **Within 48 hours**: Re-scan similar assets, deploy detection fix
5. **Within 1 week**: Incident review, method improvement plan

### 11.2 Breach Assessment

DPO and legal assess whether false negative constitutes notifiable breach under applicable regulations (GDPR, CCPA, HIPAA, state laws).

---

## 12. Related Policies

* Data Profiling Policy (GOV-001)
* Privacy & Regulatory Mapping Policy (GOV-002)
* Record Approval Workflow Policy (GOV-004)

---

## 13. Policy Review

This policy will be reviewed annually or upon:
* False negative incidents
* Detection method capability changes
* Regulatory requirement changes
* Gold set expansion or refresh

---

**Document Control**:
* **Created**: 2025-01-XX
* **Last Updated**: 2025-01-XX
* **Next Review**: 2026-01-XX
* **Owner**: Chief Data Officer
* **Co-Owner**: Data Privacy Officer
