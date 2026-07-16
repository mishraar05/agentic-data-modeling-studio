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
| `D23-01` | Exact Personal Auto proof slice | Solution owner + source owner | metadata integration | source system, catalog, schema, connected Policy/Claims tables, LOB/domain, in/out scope | `OPEN` |
| `D23-02` | Execution identities and privileges | Platform/security owner + source owner | any source/output integration | dev/test/prod principals, source `USE/SELECT`, output write, job/run and document access | `OPEN` |
| `D23-03` | Profiling run modes and resource policy | Data owner + platform owner | profiling build acceptance | permitted modes, sampling method, table/row/byte/query/time/concurrency limits | `OPEN` |
| `D23-04` | Sensitive/raw-value and suppression policy | Privacy/data governance owner | profiling execution | classification inputs, allowed metrics/distributions, minimum-count suppression, masking, raw-value prohibition/exception | `OPEN` |
| `D23-05` | Profile/evidence retention | Data governance owner | persistence build acceptance | retention periods, deletion/legal hold, allowed query text/values in Delta, logs and MLflow | `OPEN` |
| `D23-06` | Supplied-document and AI extraction policy | Document owner + security/privacy owner | document extraction | authorized locations/formats, entitlements, region/compliance, permitted AI function/endpoint, retention and citation requirements | `OPEN` |
| `D23-07` | First runtime-eligible knowledge-pack subset | Knowledge owner + required SMEs/reviewers | Increment-3 positive integration | exact pack/version/modules, authorization, effective dates, approval and runtime eligibility | `OPEN` |
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

- No exact proof-slice source/table allow-list is recorded.
- No project knowledge pack is both `APPROVED` and `runtime_eligible: true`.
- Profiling privacy, suppression, sampling and query budgets are not recorded.
- Quantitative evidence/context readiness thresholds are not recorded.
- `SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md` null-byte cleanup is complete; its text structure remains readable.

These do not prevent specification or isolated negative-path development. They prevent the affected integration or production acceptance gate.
