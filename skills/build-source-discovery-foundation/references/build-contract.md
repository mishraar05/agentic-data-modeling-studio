# Source Discovery Foundation Build Contract

## Contents

1. Boundary and prerequisites
2. Work-package ownership
3. Project placement
4. Human-decision gates
5. State and mutation rules
6. Builder evidence

## 1. Boundary and prerequisites

This build advances the Reconstructed Source Data Dictionary by creating the
deterministic evidence and context foundation. It is reusable across LOBs and
domains and does not contain Personal Auto facts.

The build consumes, and never redefines, approved contracts for control,
snapshots, sets, evidence, requirements, decisions, findings, questions,
dependencies and context. The contract dependency matrix is the `I23-00` exit
artifact. Producer implementation must not begin while that matrix contains an
unowned or ambiguous output.

The governing implementation sources are:

- `docs/architecture/source-data-dictionary/INCREMENT_2_SOURCE_ONBOARDING_IMPLEMENTATION_SPEC.md`;
- `docs/architecture/source-data-dictionary/INCREMENT_3_CONTEXT_ASSEMBLY_IMPLEMENTATION_SPEC.md`;
- `docs/architecture/source-data-dictionary/INCREMENT_2_3_GENIE_CODE_BUILD_HANDOFF.md`;
- `docs/architecture/source-data-dictionary/INCREMENT_2_3_HUMAN_DECISION_REGISTER.md`.

Read them from the repository. This reference provides routing and invariants,
not a competing specification.

## 2. Work-package ownership

| Work package | Owned build outcome | Required exit evidence |
|---|---|---|
| `I23-00` | Contract/task dependency matrix | Every output maps to exactly one contract/version; owner accepts matrix |
| `I23-01` | Runtime request, authorization snapshot and durable state | Invalid/unauthorized scope fails before source access; idempotency/concurrency tests |
| `I23-02` | Complete metadata snapshot | Every requested object has success/failure; attributes reconcile; privilege-loss test |
| `I23-03` | Controlled profile snapshot | Run mode/policy enforced; suppression before write; approximation provenance; leakage tests |
| `I23-04` | Supplied evidence and requirements | Entitlement/fingerprint/location/provenance retained; injection and missing-locator tests |
| `I23-05` | Immutable evidence-set manifest | Contract/reference/coverage/policy gates; accepted `EVIDENCE_READY` thresholds |
| `I23-06` | Exact authorized knowledge selection | Candidate/latest/ambiguous/fingerprint/effective-date paths fail closed |
| `I23-07` | Minimal evidence and decision selection | Engagement/time/supersession/provenance/budget isolation tests |
| `I23-08` | Immutable context snapshot and invalidation graph | Reproducible fingerprint; dependency-change behavior; accepted `CONTEXT_READY` thresholds |

Phase A is `I23-01..05`. Phase B is `I23-06..08`. `I23-00` gates both.

## 3. Project placement

Use these ownership boundaries unless an approved contract requires a narrower
placement:

```text
resources/source_discovery.job.yml
src/agentic_data_modeler/control/
src/agentic_data_modeler/source_adapters/
src/agentic_data_modeler/evidence/
src/agentic_data_modeler/context/
src/agentic_data_modeler/persistence/
src/workflows/
tests/unit/
tests/integration/
tests/security/
tests/fixtures/synthetic/
```

Keep one shared contract validator. Keep workflow files thin. Do not place
semantic answers, pack content or engagement values in code or Skills.

The job graph is:

```text
validate_scope
  -> register_work_package
  -> snapshot_source_metadata
  -> profile_source
  -> normalize_supplied_evidence
  -> verify_evidence_ready
  -> select_authorized_knowledge
  -> resolve_prior_decisions
  -> resolve_task_evidence
  -> assemble_context_snapshot
  -> validate_context_ready
```

Per-run values use Lakeflow job parameters. Deployment variables may supply
environment defaults but cannot lock engagement scope at deployment time.

## 4. Human-decision gates

| Decision | Gates |
|---|---|
| `D23-01` | Live proof-slice metadata access |
| `D23-02` | Any live source/output integration |
| `D23-03` | Profiling mode and resource policy |
| `D23-04` | Sensitive/raw-value and suppression policy |
| `D23-05` | Profile/evidence persistence and retention acceptance |
| `D23-06` | Live supplied-document extraction |
| `D23-07` | Positive project knowledge-selection path |
| `D23-08` | Production knowledge applicability/effective-date behavior |
| `D23-09` | Deployed compute/runtime/network identity |
| `D23-10` | `EVIDENCE_READY` transition |
| `D23-11` | `CONTEXT_READY` transition |
| `D23-12` | Recovery and invalidation acceptance |

An open decision does not block interface definition, negative tests or isolated
synthetic fixtures. It blocks the affected live or positive path. A Skill or
builder cannot accept the decision.

## 5. State and mutation rules

- Persist only contract-valid complete records as ready.
- Keep successful snapshots immutable.
- Return the existing output for an identical idempotency key.
- Create a new version when a pinned input, policy, contract, adapter or selector
  version changes.
- Preserve historical snapshots after invalidation.
- Keep source reads read-only and solution writes within solution-owned stores.
- Keep `SOURCE_FACT`, `DOCUMENT_CLAIM`, `GOVERNED_INPUT`, `REQUIREMENT`,
  `INFERENCE`, `HUMAN_DECISION` and `UNRESOLVED` distinct.
- Do not change governing documents, decision states, approval states or pack
  runtime eligibility from the build plane.

## 6. Builder evidence

Every work package handoff records:

- contract/version implemented;
- files changed;
- positive, negative, security and idempotency tests;
- bundle validation evidence where applicable;
- state-transition and record-count evidence;
- decision/policy references used;
- unresolved contract or governance blockers;
- log/trace leakage inspection; and
- a no-governance-mutation attestation.

Use the packaged YAML template and validator. A valid handoff is necessary but
not sufficient for architecture acceptance or production readiness.
