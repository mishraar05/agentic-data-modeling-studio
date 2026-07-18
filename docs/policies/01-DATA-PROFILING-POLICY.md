# Data Profiling Policy

**Policy Number**: GOV-001  
**Version**: 1.0.0  
**Effective Date**: 2025-01-XX  
**Approved By**: Chief Data Officer  
**Source**: INCREMENT_1_GOVERNANCE_REVIEW.md, Area 2, Question 1  
**Review Cycle**: Annual

---

## 1. Purpose

This policy establishes mandatory data profiling requirements for all data assets entering the Agentic Data Modeling Studio catalog. Profiling ensures data quality, supports PII detection, enables informed governance decisions, and provides audit trails for regulatory compliance.

---

## 2. Scope

This policy applies to:
* All tables and datasets onboarded to the catalog
* All profiling tiers (T1, T2, T3)
* All projects and domains
* External vendor data, third-party SaaS data, and internal sources

---

## 3. Policy Statement

**Profiling is mandatory by default** with **tiered depth** and a **narrow exception path**.

### 3.1 Profiling Depth Tiers

| Tier | Contents | Applies To | Mandatory For |
|------|----------|------------|---------------|
| **T1 — Structural** | Row count, null %, distinct %, min/max, length, type conformance | Every table, always | All assets without exception |
| **T2 — Statistical + Pattern** | Distributions, value frequency, format/pattern detection, PII candidate detection | Customer-facing, regulated, or PII/PHI-bearing domains | LTC Claims, customer data, financial data, health data |
| **T3 — Relational + Rule** | Cross-table RI, orphan detection, business-rule inference | Critical domains or on request | As requested by steward or CDO |

### 3.2 Exceptions

Each exception requires:
* Named approver (Steward or CDO)
* Documented reason
* Expiry date (never perpetual)
* Visible banner on published documentation

#### Approved Exception Categories:

1. **No read access** — External vendor, third-party SaaS, source not yet onboarded
   * **Action**: Publish structure-only, banner-flagged `UNPROFILED`
   * **Approver**: Steward
   * **Expiry**: 90 days or upon access grant

2. **Empty or greenfield table** — Below row threshold (< 100 rows)
   * **Action**: Profiling deferred to first load, auto-queued
   * **Approver**: System automatic
   * **Expiry**: First load event or 30 days

3. **Restricted data with no accessible copy** — Profile executed in-place by data owner, or deferred
   * **Action**: Data owner executes profiling in restricted environment
   * **Approver**: CDO
   * **Expiry**: 60 days

#### Explicitly NOT Exceptions:

* **Emergency/quick-doc** — T1 profiling is cheap. Schedule pressure is not a governance exception.
* **Dev/test databases** — These get profiled but downgraded, not skipped. Data is unrepresentative, so profile for structure and flag the doc "profiled against non-representative data — no DQ or distribution inference valid."

---

## 4. Hard Gate

A document cannot reach **Certified/Published** status without:
* A completed profiling run appropriate to its tier, OR
* An approved, unexpired exception

---

## 5. Responsibilities

### 5.1 Data Stewards
* Request appropriate profiling tier for new assets
* Review profiling results before publication
* Submit exception requests with justification
* Monitor exception expiry dates

### 5.2 Chief Data Officer
* Approve T3 profiling requests
* Approve exception requests requiring CDO authority
* Review quarterly profiling compliance metrics

### 5.3 Technical Teams
* Execute profiling runs per tier specifications
* Maintain profiling automation and tooling
* Report profiling failures and performance issues

---

## 6. Compliance Monitoring

### 6.1 Metrics
* % of published assets with valid profiling
* % of assets operating under approved exceptions
* Average time from onboarding to profiling completion
* Exception approval turnaround time

### 6.2 Reporting
* Quarterly compliance report to CDO
* Monthly exception expiry report to stewards
* Ad-hoc reports for audit requests

---

## 7. Policy Violations

Violations include:
* Publishing without profiling or approved exception
* Using expired exceptions
* Bypassing hard gate controls

**Remediation**:
* Immediate unpublishing of non-compliant assets
* Mandatory profiling before republication
* Escalation to CDO for pattern violations

---

## 8. Related Policies

* PII Detection Standards (GOV-003)
* Privacy & Regulatory Mapping Policy (GOV-002)
* Record Approval Workflow Policy (GOV-004)

---

## 9. Policy Review

This policy will be reviewed annually or upon:
* Regulatory requirement changes
* Technology capability changes
* Compliance audit findings
* Business process changes

---

**Document Control**:
* **Created**: 2025-01-XX
* **Last Updated**: 2025-01-XX
* **Next Review**: 2026-01-XX
* **Owner**: Chief Data Officer
