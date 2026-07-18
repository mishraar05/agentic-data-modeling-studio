# Emergency Override Procedures

**Policy Number**: GOV-006  
**Version**: 1.0.0  
**Effective Date**: 2025-01-XX  
**Approved By**: Chief Data Officer  
**Source**: INCREMENT_1_GOVERNANCE_REVIEW.md, Area 4, Question 3  
**Review Cycle**: Annual

---

## 1. Purpose

This policy establishes emergency procedures for handling urgent corrections and critical data governance issues while preserving audit trail integrity. The policy balances operational urgency with compliance requirements.

---

## 2. Scope

This policy applies to:
* All historical record corrections
* All approved definition corrections
* All emergency redaction scenarios
* All break-glass procedures

---

## 3. Core Principle

**Universal Rule**: Additive-only corrections via new records (never mutation).

**Narrow Break-Glass**: Dual-control redaction ONLY when the record itself contains PII/PHI that must be removed.

**Critical Insight**: Most "emergencies" don't need overrides — they need better mechanisms.

---

## 4. Scenario A: Historical Record Error with Regulatory Exposure

### 4.1 Example Scenario

**Situation**: 2024 profiling run recorded "SSN detected in customer_notes: NO". 2025 audit discovers SSNs were actually present (false negative).

### 4.2 What NOT to Do

**❌ WRONG**: Mutate the 2024 record to say "YES"

**Why This Is Wrong**:
* Destroys regulatory defense
* The 2024 record is TRUE: it accurately says "detector reported NO SSN"
* The problem is the detector, not the record
* Editing the record after learning of the exposure:
  * Deletes proof of good faith operation
  * Makes record consistent with having known since 2024
  * Creates documented instance of altering records under audit
  * Converts control failure into spoliation

### 4.3 What TO Do (Additive-Only, Normal Approval Speed)

1. **New 2025 observation**: "SSNs confirmed present, N matches, detected by [method]"
2. **Forward-annotation on 2024 record**: "Contradicted by [2025 finding]. This run used detector v1.2, which had known false-negative gap on unformatted 9-digit sequences in free text"
3. **Root-cause**: Fix detector, add to gold set, re-scan domain per PII Detection Standards (GOV-003)

### 4.4 Critical Separation

**Data-Plane Urgency ≠ Metadata-Plane Override**

* **Data plane** (urgent, minutes): Mask the column, restrict the role, revoke access
* **Metadata plane** (normal, hours/days): Add correcting observation, annotate

Unity Catalog policy actions executable in minutes via separate change path. Never let data-plane urgency leak into metadata-plane immutability.

---

## 5. Scenario B: Approved Definition Blocking Critical Work

### 5.1 Example Scenario

**Situation**: Wrong data dictionary definition. Production incident in progress, teams need correct definition NOW. Normal approval chain takes 2-3 business days. Business losing money by the hour.

### 5.2 Critical Distinction

Teams need to **KNOW** the correct definition in 5 minutes. They do NOT need it to be **OFFICIALLY APPROVED** in 5 minutes.

**Split "knowing" from "official"**.

### 5.3 CONTESTED Flag Mechanism (Additive, Instant, No Approval)

Any steward can attach contest note to approved record instantly, unilaterally:

```
⚠️ CONTESTED 2026-07-17 09:14 by A. Mishra — 
"policy_status='A' means active-premium-paying, NOT active-claim. 
See INC-4471." Under review.
```

### 5.4 How It Works

* Record stays APPROVED (status untouched)
* Contest note is new, additive record (nothing mutated)
* Readers see correction in UI immediately, above the fold
* Downstream consumers can trigger on contest event
* Correction then enters normal steward → CDO chain within 48h
* Either supersedes the record or contest is withdrawn (also additively, with reason)

**No approval was bypassed** because no approval occurred. Additive-only architectures don't need emergency paths — the emergency path is just writing, which was always unrestricted.

### 5.5 When Catalog Is in Critical Path

**If 2-3 day approval genuinely blocks incident resolution**: The bug is that the catalog is in the incident's critical path. That's an architecture problem to fix, not an override to build.

**Remediation**:
* Systems should cache/replicate operational metadata
* Production systems should not hard-depend on approval-gated metadata
* Engineering practices review required

---

## 6. Scenario C: Record IS the Harm (Break-Glass Required)

### 6.1 When Break-Glass Is Needed

Additive-only handles everything **except** when the record's own content is the violation.

**Examples**:
* Profiling observation stored sample values — and those samples are the SSNs
* Catalog readable by 400 people is now unauthorized disclosure
* DQ finding embeds claimant name in error message → PHI in general-access surface
* Steward's free-text note contains MRN

### 6.2 Why Different

Appending "please disregard the SSNs above" accomplishes nothing. The exposure is the bytes. Must physically alter an immutable record.

**Here HIPAA minimum-necessary and GDPR Art. 17 outrank immutability design.**

### 6.3 Redaction, Not Deletion or Editing

| Preserved | Removed |
|-----------|---------|
| Record ID, permalink, hash chain, timestamps | The offending payload field only |
| Full audit trail, authorship, lineage edges | — |
| Statistical results (counts, patterns, nulls) | — |
| The fact that a run occurred at T | — |

**Field Becomes**:
```
[REDACTED 2026-07-17 — contained unmasked PII in sample values. 
Dual-control auth: A. Mishra + R. Sen. Ref: GOV-1234]
```

Record still exists, still resolves, still proves run happened. Only bytes constituting violation are gone.

**Tombstone the payload; keep the skeleton.**

---

## 7. Dual Control Mechanism

### 7.1 Why Dual Control, Not Break-Glass CDO

| | Break-glass CDO | Dual Control |
|---|-----------------|--------------|
| **3am Sunday, CDO on flight** | Blocked | Works |
| **Erosion risk** | High — becomes "fast path"; org routes urgent things to CDO; CDO approves unread within a quarter | Low — two people must be careless simultaneously |
| **Coerced/compromised single account can vanish content** | Yes | No |

### 7.2 Dual Control Requirements

* **Two authorized people** from small named roster (5-7 people)
* **Both must authenticate** within 1-hour window
* **CDO is notified**, not required — preserves oversight without single point of availability failure
* Invocation is trivially easy and impossible to do quietly

### 7.3 Authorized Roster

Maintained by CDO, reviewed quarterly:
* Data stewards (2-3 people)
* Data Privacy Officer
* Security lead
* Technical lead
* CDO (optional, not required)

---

## 8. Anti-Abuse Controls — Make It Loud, Not Hard

### 8.1 Transparency Mechanisms

**On trigger**:
* Auto-notify CDO + DPO + security channel
* Auto-file governance ticket
* Auto-add to next governance forum agenda (non-removable)

### 8.2 Ratification Window

* **72-hour ratification** required
* **Not ratified** → Escalates automatically as control incident
* **Post-action review** mandatory
* Neither invoker may be reviewer

### 8.3 Override Log Immutability

**Override log is itself append-only and can NEVER be break-glassed.**

Recursion stops here, permanently, no exceptions.

---

## 9. Design It So It Never Fires — Never Store Raw Sample Values

### 9.1 Prevention at Design Time

For anything Tier A/B (PII Detection Standards, GOV-003) or in PHI-density domain, profiling records **pattern, never value**:

✅ **Record**: 
```
pattern: ###-##-#### 
matches: 847 
distinct_formats: 3 
confidence: 0.98
```

❌ **DON'T Record**: 
```
samples: ["123-45-6789", "987-65-4321"]
```

### 9.2 Rationale

If SSN never enters catalog, never need to redact it. Eliminates entire break-glass category at design time — exactly where to solve it, given LTC Claims' PHI density.

---

## 10. CONTESTED Flag Procedures

### 10.1 Who Can Contest

* Data stewards
* Subject matter experts
* CDO
* Data governance team members

### 10.2 Contest Process

1. **Flag approved record** with CONTESTED status
2. **Provide correction** in contest note (50-500 characters)
3. **Reference evidence** (ticket ID, document, incident)
4. **System auto-notifies** record owner and CDO
5. **48-hour SLA** for steward review
6. **Resolution paths**:
   * Supersede record (enters full approval chain)
   * Withdraw contest (additive note explaining why)
   * Escalate to CDO (if disagreement)

### 10.3 Contest Resolution Tracking

* All contests tracked in governance dashboard
* Overdue contests escalate automatically
* Pattern analysis quarterly (frequent contests = definition quality issue)

---

## 11. Break-Glass Redaction Procedures

### 11.1 Invocation Process

**Step 1: Identify Violation**
* Steward or DPO identifies PII/PHI in catalog record
* Assess: Is this a data-plane issue (mask table) or metadata-plane issue (redact catalog)?

**Step 2: Attempt Normal Remediation First**
* Can we deprecate and supersede? (preferred)
* Can we restrict access instead? (second choice)
* Only proceed to break-glass if record content itself must be physically altered

**Step 3: Dual Control Invocation**
* First authorized person initiates redaction request
* System generates ticket, notifies roster
* Second authorized person must approve within 1 hour
* Both must provide written justification

**Step 4: Execute Redaction**
* System performs field-level redaction
* Preserves record skeleton (ID, timestamp, metadata)
* Inserts redaction tombstone with reason and authority
* Logs full audit trail

**Step 5: Immediate Notifications**
* CDO, DPO, security team notified within 5 minutes
* Governance ticket auto-filed
* Added to next governance meeting agenda

**Step 6: 72-Hour Ratification**
* CDO reviews justification and execution
* DPO validates legal/regulatory basis
* If not ratified → Control incident investigation

---

## 12. Responsibilities

### 12.1 Data Stewards
* Use CONTESTED flag for urgent corrections
* Propose break-glass redaction only when required
* Participate in dual control as authorized roster member
* Complete contest resolution within 48h SLA

### 12.2 Chief Data Officer
* Approve contested record supersessions
* Ratify break-glass redactions within 72h
* Maintain authorized roster for dual control
* Review quarterly override metrics

### 12.3 Data Privacy Officer
* Validate legal basis for break-glass redactions
* Assess breach notification requirements
* Participate in post-action reviews
* Co-ratify break-glass invocations

### 12.4 Technical Teams
* Implement CONTESTED flag mechanism
* Maintain dual-control break-glass controls
* Ensure override log immutability
* Generate transparency alerts

---

## 13. Metrics and Monitoring

### 13.1 Target Metrics

| Signal | Target | Interpretation |
|--------|--------|----------------|
| **Break-glass invocations** | < 2/year | Firing monthly = normal path too slow → fix path, don't normalize override |
| **Contest flags** | Healthy at any volume | This is the system working |
| **Contests unresolved > 48h** | 0 | Stale contest is worse than no contest |
| **Break-glass traceable to stored sample values** | 0 | Each one is design defect, not governance event |

### 13.2 Reporting

* **Real-time**: Break-glass invocation alerts
* **Weekly**: Contest aging report
* **Monthly**: Override metrics dashboard
* **Quarterly**: Pattern analysis and policy effectiveness review

---

## 14. Policy Violations

Violations include:
* Mutating historical records without break-glass procedure
* Using break-glass for non-PII/PHI scenarios
* Single-person break-glass invocation
* Bypassing ratification window
* Storing sample PII/PHI values in profiling (design violation)

**Remediation**:
* Immediate control incident investigation
* Audit trail reconstruction
* Enhanced monitoring for pattern
* Design fixes to prevent recurrence

---

## 15. Training Requirements

### 15.1 Mandatory Training for Stewards

* Additive-only principles and rationale
* CONTESTED flag usage and workflow
* When to escalate vs self-resolve
* Data-plane vs metadata-plane separation

### 15.2 Mandatory Training for Dual Control Roster

* Break-glass justification criteria
* Dual control procedures
* Redaction scope limits
* Post-action review participation

---

## 16. Integration with Other Policies

This policy integrates with:
* **PII Detection Standards (GOV-003)**: Defines sample value prohibition
* **Record Approval Workflow Policy (GOV-004)**: Defines normal approval paths
* **Record Deprecation Policy (GOV-005)**: Defines CONTESTED flag usage
* **Privacy & Regulatory Mapping Policy (GOV-002)**: Defines PII/PHI classification

---

## 17. Policy Review

This policy will be reviewed annually or upon:
* Break-glass invocation (immediate review)
* Pattern of contested records (quarterly)
* Regulatory requirement changes
* Control incident findings

---

**Document Control**:
* **Created**: 2025-01-XX
* **Last Updated**: 2025-01-XX
* **Next Review**: 2026-01-XX
* **Owner**: Chief Data Officer
* **Co-Owner**: Data Privacy Officer

---

## Appendix A: Quick Reference Decision Tree

```
NEED URGENT CORRECTION?
│
├─ Historical record error?
│  └─ ✅ Add new observation, annotate old one (additive-only)
│
├─ Approved definition wrong?
│  ├─ Blocks incident response?
│  │  └─ ✅ CONTESTED flag (instant, no approval)
│  └─ Normal business need?
│     └─ ✅ Supersede (steward → CDO approval)
│
└─ Record contains PII/PHI?
   ├─ Can deprecate/restrict instead?
   │  └─ ✅ Prefer deprecation
   └─ Record itself is the exposure?
      └─ ⚠️  Break-glass dual control redaction
```
