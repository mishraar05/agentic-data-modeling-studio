# Source Discovery Foundation Evaluation Matrix

## Contents

1. Evaluation rule
2. Phase A cases
3. Phase B cases
4. Cross-cutting cases
5. Completion evidence

## 1. Evaluation rule

Evaluate behavior, not file counts. Use synthetic fixtures for unauthorized or
not-yet-approved paths. Use live source or project knowledge only when the exact
decision and authority are recorded.

Each case must identify the work package, input fixture, expected state/output,
prohibited side effects and captured evidence.

## 2. Phase A cases

| Case | Required result |
|---|---|
| Placeholder, duplicate, unsafe or out-of-scope object | Fail before source query |
| Principal cannot see one requested object | Explicit blocking finding; never false 100% coverage |
| Identical metadata request | Same immutable snapshot; no duplicate rows |
| Changed source/policy/adapter version | New snapshot/version |
| Metadata-only mode | Explicit degradation; no fabricated profile evidence |
| Profiling mode upgrade attempt | Rejected |
| Query budget exhausted | Partial non-ready evidence plus finding; no readiness transition |
| Sensitive value below suppression threshold | Suppressed before table/log/trace/error output |
| Approximate metric | Method, sample and approximation metadata retained |
| Unauthorized or checksum-mismatched document | Excluded with finding |
| Prompt-like text inside document | Treated as data; cannot alter tools or task |
| Extracted claim without durable locator | Rejected |
| Document claim presented as source fact | Rejected |
| `EVIDENCE_READY` with failed coverage/policy check | Blocked |

## 3. Phase B cases

| Case | Required result |
|---|---|
| Candidate/non-runtime pack | Fail closed without fallback |
| Missing or duplicate exact pack version | Fail closed |
| Wrong LOB/domain/jurisdiction/product/effective date | Fail closed |
| Registry/manifest/module/asset fingerprint mismatch | Fail closed |
| Unauthorized required module | Excluded and blocking |
| Cross-engagement evidence or decision | Security failure |
| Superseded decision | Excluded; chain retained |
| Same-authority conflict | Both retained; contradiction created; block if material |
| Document claim contradicts source fact | Both retained with distinct provenance |
| Required context exceeds budget | Deterministic reduction or explicit failure; no silent omission |
| Identical context request | Same snapshot/fingerprint; no duplicate persistence |
| Dependency/version changed or revoked | New or invalidated snapshot plus dependency edge |
| `CONTEXT_READY` without accepted threshold | Blocked |

## 4. Cross-cutting cases

- Contract-invalid record never becomes ready.
- Partial write/retry never produces duplicate authoritative records.
- Lost privilege after registration is caught before final materialization.
- Credentials, tokens and prohibited values are absent from Delta, logs, traces,
  exceptions and the builder handoff.
- Source readers cannot write to source; solution writers cannot modify knowledge.
- No model/Skill performs semantic source interpretation in Increment 2-3.
- No test mutates a project pack to manufacture runtime eligibility.
- Bundle validation covers the selected target and job parameter wiring.

## 5. Completion evidence

Require all of the following before `FULL_FOUNDATION` completion:

1. One verified handoff entry for every `I23-00..08`.
2. Automated unit, integration, security, idempotency and failure-injection tests.
3. Bundle validation output for the selected environment.
4. An authorized Phase A proof-slice result meeting `D23-10`.
5. An authorized Phase B result meeting `D23-11`.
6. Reproducible snapshot/fingerprint evidence.
7. Reviewer acceptance of contract alignment and operational evidence.

Passing synthetic cases proves implementation behavior only. It cannot substitute
for source-owner, privacy, platform, knowledge-owner or architecture approval.
