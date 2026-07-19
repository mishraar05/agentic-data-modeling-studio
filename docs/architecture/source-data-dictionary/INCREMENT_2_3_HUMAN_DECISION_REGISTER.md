# Increment 2–3 Human Decision Register

**Status:** Open decision register  
**Rule:** Missing decisions fail closed. Claude/Codex may structure the options and impact; Genie Code may implement the selected policy; neither may choose or approve the decision.

## Decision states

- `OPEN` — no authorized decision is recorded.
- `PROPOSED` — options exist but the decision owner has not accepted one.
- `ACCEPTED` — the decision, owner and effective scope are recorded.
- `SUPERSEDED` — replaced by a linked later decision.

## Blocking decisions

| ID | Decision | Owner role | Blocks | Required recorded outcome | Current state |
|---|---|---|---|---|---|
| `D23-01` | Exact Personal Auto proof slice | Solution owner + source owner | metadata integration | source system, catalog, schema, connected Policy/Claims tables, LOB/domain, in/out scope | `ACCEPTED` |
| `D23-02` | Execution identities and privileges | Platform/security owner + source owner | any source/output integration | dev/test/prod principals, source `USE/SELECT`, output write, job/run and document access | `ACCEPTED` |
| `D23-03` | Profiling run modes and resource policy | Data owner + platform owner | profiling build acceptance | permitted modes, sampling method, table/row/byte/query/time/concurrency limits | `ACCEPTED` (synthetic dev only) |
| `D23-04` | Sensitive/raw-value and suppression policy | Privacy/data governance owner | profiling execution | classification inputs, allowed metrics/distributions, minimum-count suppression, masking, raw-value prohibition/exception | `ACCEPTED` (synthetic dev only) |
| `D23-05` | Profile/evidence retention | Data governance owner | persistence build acceptance | retention periods, deletion/legal hold, allowed query text/values in Delta, logs and MLflow | `ACCEPTED` (synthetic dev only) |
| `D23-06` | Supplied-document and AI extraction policy | Document owner + security/privacy owner | document extraction | authorized locations/formats, entitlements, region/compliance, permitted AI function/endpoint, retention and citation requirements | `OPEN` |
| `D23-07` | First runtime-eligible knowledge-pack subset | Knowledge owner + required SMEs/reviewers | Increment-3 positive integration | exact pack/version/modules, authorization, effective dates, approval and runtime eligibility | `ACCEPTED` |
| `D23-08` | Knowledge authorization/effective-date policy | Knowledge owner + architecture/security owner | context selector completion | subject/role access, jurisdiction/product applicability, effective-date and revocation/supersession rules | `OPEN` |
| `D23-09` | Compute and deployment policy | Platform owner | deployed integration | workspace/region, serverless/warehouse/cluster choices, approved runtime, network and service-principal policy | `OPEN` |
| `D23-10` | Increment 2 readiness thresholds | Solution owner + source SME | `EVIDENCE_READY` | inventory coverage, permitted failure rate, profile coverage by mode, extraction citation rate, latency/cost ceilings | `OPEN` |
| `D23-11` | Increment 3 readiness thresholds | Solution owner + architecture/security owner | `CONTEXT_READY` | required-section completeness, conflict policy, budget limits, reproducibility, latency/cost ceilings | `OPEN` |
| `D23-12` | Recovery and invalidation policy | Architecture/operations owner | operational acceptance | retry limits, checkpoint retention, replay authority, stale snapshot behavior, recovery objectives | `OPEN` |
| `D23-13` | Governing-document repair authority | Architecture owner | architecture sign-off | controlling architecture restored to 238 lines with a complete §7; flow document contains no null bytes | `ACCEPTED` |

### Accepted decision record: D23-13 v1

- **Decision owner:** Solution/architecture owner, recorded from owner direction.
- **Approval time:** `2026-07-16T13:11:10+05:30`.
- **Effective scope:** repository-wide governing architecture and Source Discovery flow documents.
- **Outcome:** accept Claude's restored `AGENT_SOLUTION_ARCHITECTURE.md`; retain the repaired Source Discovery flow text.
- **Verification evidence:** architecture is UTF-8-readable, has 238 lines, contains §§1–7 and ends with the required skill declaration list; the Source Discovery flow has 359 readable lines and zero null bytes.
- **Implementation consequence:** remove only the document-integrity blocker from KM2. Contract publication, knowledge-pack approval/runtime eligibility and remaining D23 decisions are unchanged.
- **Re-review trigger:** any corruption, truncation or material change to either governing document.

### Accepted decision record: D23-03 v1 — synthetic development

- **Decision owner:** Solution owner acting as data/platform owner for the isolated synthetic-development proof slice; recorded from explicit owner approval.
- **Approval time:** `2026-07-18T18:47:21+05:30`.
- **Effective scope:** the recorded P&C Personal Auto / Policy solution run, the seven authorized `insurance_source_discovery.gw_pc_bronze` tables, DEV workspace only.
- **Outcome:** contract-owned `RESTRICTED` mode; full-scan aggregate counts; at most 7 tables, 62 attributes and 7 queries; concurrency 1; 120-second per-query acceptance limit and 900-second total task limit.
- **Rejected alternatives:** `FULL`, value distributions, concurrent execution and an unbounded scan, because they add privacy/cost risk without being needed to prove the first controlled pipeline.
- **Evidence:** owner approval in the project execution thread; policy `GOV-001@1.0.0`.
- **Effective period:** effective immediately; review by `2026-08-17`; no production authority.
- **Implementation consequence:** template-only aggregate profiling may execute; a limit violation fails the task and cannot advance `PROFILE_READY`.
- **Re-review trigger:** different engagement/work package, table scope, workspace, mode, metric set, limits or production use.

### Accepted decision record: D23-04 v1 — synthetic development

- **Decision owner:** Solution owner acting as privacy/data-governance owner for the isolated synthetic-development proof slice; recorded from explicit owner approval.
- **Approval time:** `2026-07-18T18:47:21+05:30`.
- **Effective scope:** identical to `D23-03 v1`.
- **Outcome:** permit only row, null and exact distinct counts. Prohibit retained raw values, minima/maxima, top values, patterns, distributions and generated SQL text in Delta, logs, traces or exceptions.
- **Rejected alternatives:** raw samples and bounded distributions, because the first proof needs control evidence rather than value-level semantic depth.
- **Evidence:** owner approval in the project execution thread; privacy-by-default architecture constraint.
- **Effective period:** effective immediately; review by `2026-08-17`; no production authority.
- **Implementation consequence:** the adapter emits counts only and fails before execution if a prohibited metric or retention flag is requested.
- **Re-review trigger:** any value-bearing metric, privacy-classification inference, external model use or broader scope.

### Accepted decision record: D23-05 v1 — synthetic development

- **Decision owner:** Solution owner acting as data-governance owner for the isolated synthetic-development proof slice; recorded from explicit owner approval.
- **Approval time:** `2026-07-18T18:47:21+05:30`.
- **Effective scope:** identical to `D23-03 v1`.
- **Outcome:** retain aggregate-only development profile evidence for 30 days; retain query references and template versions but never query text or source values. No legal hold applies to this synthetic slice.
- **Rejected alternatives:** indefinite development evidence and retained query/value payloads, because they are unnecessary for proof-slice assessment.
- **Evidence:** owner approval in the project execution thread.
- **Effective period:** evidence produced under this decision expires 30 days after capture; review by `2026-08-17`; no production authority.
- **Implementation consequence:** persisted evidence carries the policy/expiry declaration; automated physical cleanup remains an operational acceptance requirement before production use.
- **Re-review trigger:** production use, legal hold, changed retention period or any value-bearing evidence.

### Accepted addendum: D23-03/D23-04 v2 — DQX synthetic development

- **Decision owner:** Solution owner acting as data/platform/privacy owner for the isolated synthetic-development slice; recorded from the explicit instruction to deploy and bring the DQX profiling refactor after the DQX trade-off was explained.
- **Approval time:** `2026-07-18T19:54:13+05:30`.
- **Effective scope:** the recorded P&C Personal Auto / Policy solution run, the frozen `SCHEMA_ALL_TABLES` manifest for `insurance_source_discovery.gw_pc_bronze`, DEV workspace only.
- **Outcome:** use pinned `databricks-labs-dqx==0.15.0` programmatically with sampling and row limits disabled. DQX may calculate its standard rich summary transiently inside the isolated synthetic job. The governed projection persists only row, null and exact distinct counts; generated DQX rules, minima/maxima, distributions, patterns, query text and source values are discarded and must not enter Delta evidence, logs, traces or exceptions.
- **Evidence:** owner instruction in the project execution thread; DQX public profiler API and pinned engine version; policy `GOV-001@1.0.0`.
- **Implementation consequence:** DQX sits behind a versioned adapter; scope, budgets, persistence, retention, provenance, idempotency and workflow state remain solution-owned deterministic controls.
- **Re-review trigger:** production use, non-synthetic data, a DQX version change, persisted generated rules, sampling, any value-bearing persistence, or a source manifest exceeding the approved resource budget.

### Accepted decision record: D23-07 v1 — runtime knowledge pack

- **Decision owner:** Solution owner, recorded from the explicit instruction to change the existing pack from `CANDIDATE` to `APPROVED` and set runtime eligibility to true.
- **Approval time:** `2026-07-18`.
- **Outcome:** `public_us_pnc_personal_auto@0.6.0`, its registered source set, manifest-referenced modules, glossary, code sets, modeling standards and pinned reference metadata are `APPROVED`; the registry and manifest are `runtime_eligible: true`.
- **Scope:** the pack retains its declared `US_general`, Personal Auto, party/product/coverage/policy/claims/billing/analytics scope. Runtime tasks must still select only the smallest task-applicable subset and must not scan directories or use cross-version fallback.
- **Known limitations retained:** trusted runtime readiness remains scored at `0` until independent expert evaluation is supplied; licensing-review warnings remain; FIBO concept selection remains `NOT_APPROVED`; extension placeholders do not become engagement facts; unresolved enterprise, carrier and jurisdiction details remain unresolved.
- **Implementation consequence:** exact pack selection may pass the approval/eligibility gate. This decision does not approve model artifacts, source-code mappings, jurisdiction applicability, production deployment, or cross-engagement access.
- **Remaining gate:** `D23-08` stays `OPEN`; runtime authorization, effective-date and applicability policy must be recorded before a governed context snapshot can advance to `CONTEXT_READY`.
- **Re-review trigger:** pack content/fingerprint change, legal/licensing decision, a new version, changed scope, revoked source, or production authorization.

### Accepted decision record: D23-01 v1 — source scope selection

- **Decision owner:** Solution owner + source owner, recorded from owner direction.
- **Approval time:** `2026-07-19`.
- **Effective scope:** proof slice; source catalog `insurance_source_discovery`, schema `gw_pc_bronze` (from product `gw_pc` + layer `bronze`).
- **Outcome:** source scope is selected by `proof_slice.source_scope.mode` in `config/env_config.yaml`: `partial` processes only `allow_listed_tables`; `full` processes every table in the defined `catalog.schema`.
- **Rejected alternatives:** hardcoding a fixed table list in code (brittle, not owner-controlled).
- **Evidence:** owner direction; `config/env_config.yaml` `proof_slice.source_scope`.
- **Implementation consequence:** Phase 0 scope validation reads `source_scope`; `full` enumerates tables from the catalog, `partial` uses the allow-list. Removes the source/table blocker.
- **Re-review trigger:** change of source system, catalog, schema, or a move to production data.

### Accepted decision record: D23-02 v1 — execution identity assumption

- **Decision owner:** Platform/security owner, recorded from owner direction.
- **Approval time:** `2026-07-19`.
- **Effective scope:** all SDD runtime source/output access.
- **Outcome:** service-principal permissioning is a platform/framework responsibility, not an SDD-runtime concern. The framework **assumes the configured service principal already holds the required `USE`/`SELECT` on the source and write on outputs**. The agent performs no per-run identity or grant gate.
- **Rejected alternatives:** the agent managing or verifying grants — out of scope; the platform owns IAM.
- **Evidence:** owner direction.
- **Implementation consequence:** removes `D23-02` as a blocker; no grant-management code in the agent. A denied read surfaces as a platform permissions error, not an agent decision.
- **Re-review trigger:** platform introduces per-engagement identity isolation or revokes the standing-permission assumption.

## Suggested resolution order

1. `D23-01`, `D23-02`, `D23-03`, `D23-04`, `D23-05` — unblock metadata/profiling integration.
2. `D23-06`, `D23-09` — unblock supplied-evidence extraction and deployment details.
3. `D23-10` — establish the Increment-2 exit gate.
4. `D23-07`, `D23-08` — unblock positive Increment-3 integration without weakening governance.
5. `D23-11`, `D23-12` — establish context and operational acceptance.

## Decision record requirements

Every accepted decision must contain:

- decision ID and version;
- decision owner and approval time;
- effective engagement/environment/LOB/domain/source scope;
- selected option and rejected alternatives with rationale;
- referenced policy or evidence;
- effective-from/effective-to, review date and supersession link;
- implementation consequences; and
- conditions that require re-review.

An email or chat statement is not durable authority until it is entered through the controlled decision process.

## Known current blockers

- Source scope is recorded (`D23-01`): `config/env_config.yaml` → `proof_slice.source_scope` (partial allow-list or full schema).
- Execution identity is assumed available (`D23-02`): platform-owned; the agent does not manage grants.
- A runtime-eligible knowledge pack exists (`D23-07`): `public_us_pnc_personal_auto@0.6.0`.
- Production profiling privacy, suppression, sampling, query-budget and retention decisions are not recorded. `D23-03`–`D23-05 v1` authorize only the isolated synthetic-development proof slice.
- Quantitative evidence/context readiness thresholds are not recorded.
- `SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md` null-byte cleanup is complete; its text structure remains readable.

These do not prevent specification or isolated negative-path development. They prevent the affected integration or production acceptance gate.
