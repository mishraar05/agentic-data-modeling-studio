# P&C Personal Auto Policy proof-slice assessment

**Assessment date:** 2026-07-18  
**Engagement / work package:** `E-123` / `WP-1234`  
**Charter deliverable advanced:** reconstructed Source Data Dictionary  
**Reusable need:** schema-wide source onboarding with restricted DQX profiling  

## Owner summary

The observation stage is working. The deployed job discovers every eligible
table in the authorized schema, freezes that exact list, captures metadata and
creates safe DQX counts. It does not yet explain business meaning or create the
four owner deliverables. The next valid step is governed context assembly, which
cannot enter its positive path until an exact knowledge-pack version and module
subset are approved for runtime use.

## Deployed evidence

| Check | Evidence | Result |
|---|---|---|
| First refactored run | Databricks job `56210102161162`, run `793226946096784` | all five tasks succeeded |
| Reproducibility run | Databricks job `56210102161162`, run `377724153309824` | all five tasks succeeded |
| Evidence-ready run | Databricks job `56210102161162`, run `538016131126289`, repair `1043773443579365` | all six tasks succeeded after correcting the metadata-item invariant |
| Schema coverage | frozen manifest and `profile_snapshot` | 7 of 7 tables |
| Attribute coverage | `profile_snapshot` and `profile_evidence` | 62 of 62 attributes |
| Profiler identity | `profile_snapshot.provenance.tool_version` | `dqx/0.15.0/restricted-projection/0.1.0;GOV-001@1.0.0` |
| Restricted persistence | `profile_evidence` query | 0 records contain min, max, top-value or pattern samples |
| Idempotency | two completed run records; one DQX profile snapshot | passed |
| Evidence assembly | `evidence_set_af29c7f0764bc30b8cd1d464084c4c3b` | 69 referenced items: 7 table-level metadata items and 62 attribute-profile items |
| Workflow state | `work_package.workflow_state` | `EVIDENCE_READY` |
| Local regression | full test suite | 277 passed, 2 existing skips |

The profile snapshot is
`profile_snapshot_36bacefa50e3ac252b4e792b04afe4e1`, linked to source
snapshot `source_snapshot_170b53609ed5b9e12f57980dbbfbf991`. It contains 62
attribute evidence records and no prohibited value-bearing fields.

The immutable evidence-set fingerprint is
`6bdbb80842c53bec7d4c99187b33635ffca9e14e65ed7ee659f82569911f19fa`.
Its stored item count and independently queried referenced-item count are both
69.

## Charter assessment

| Charter outcome | Current evidence | Assessment |
|---|---|---|
| Reconstructed Source Data Dictionary | source inventory and profiles exist; no semantic draft/review/publish stage exists | incomplete |
| Silver ODS model | design only | not built |
| Gold dimensional model | design only | not built |
| Attribute-level STTM | design only | not built |
| Requirement coverage, gaps and run evidence | profiling run evidence exists; downstream coverage/gaps do not | incomplete |
| Human review and durable decision reuse | App scaffold only; decision write/read loop is not implemented | not built |
| Review/portable formats | no proof-slice workbook or complete App views | not built |

Passing jobs and record counts therefore prove the observation boundary, not
completion of the proof slice. The Requirements Charter completion gate remains
open.

## Next gate

Decision `D23-07` now approves exact pack
`public_us_pnc_personal_auto@0.6.0` for runtime selection. Decision `D23-08`
must still define its engagement authorization, applicability and effective-date
rules before a governed context snapshot may advance to `CONTEXT_READY`.

Once those decisions exist, build and deploy in this order:

1. immutable governed context snapshot;
2. evidence-citing Source Data Dictionary draft and critic;
3. human review and durable decision capture;
4. approved dictionary handoff;
5. Silver, Gold, STTM and requirement-coverage drafts with review gates; and
6. Delta-backed publication plus workbook/App views and charter evaluation.

This work belongs now because governed context is the required bridge between
observed source evidence and semantic/modeling judgment. Tool-specific ETL or BI
conversion remains deferred and is not required for this gate.
