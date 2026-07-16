# Increment 2–3 Genie Code Build Handoff

**Status:** Draft build handoff; execute only after architecture review and applicable human decisions  
**Builder:** Genie Code  
**Planner/specification owner:** Claude/Codex  
**Contract owner:** Increment-1 contract specification and approved schemas

## 1. Builder mandate

Build deterministic source onboarding and context assembly. Do not add semantic inference, source-specific meaning, hard-coded answer keys, agent skills, approval authority, ontology creation, Silver/Gold/STTM behavior or proprietary ETL/BI conversion.

If an Increment-1 field or record relationship is missing, stop and raise a contract decision. Do not create a parallel contract in code.

## 2. Immediate design corrections

1. **Use job parameters for per-run scope.** The current DAB scaffold uses bundle variables for engagement, LOB, domain and source tables. Bundle variables resolve at deployment, so the deployed job cannot safely receive a new work package without redeployment. Retain environment defaults as bundle variables and expose overridable Lakeflow job parameters.
2. **Separate the source-discovery job.** Do not append Increment 2–3 tasks to a generic end-to-end modeling job in a way that crosses the approved SDD handoff boundary. Create a bounded source-discovery job/resource or explicitly rename and constrain the existing resource.
3. **Recheck governing-file integrity before building.** `D23-13` restored the architecture and removed the flow-document null bytes. Verify both files still pass that integrity baseline; stop on any new corruption or conflicting change.
4. **Do not create positive runtime behavior by changing candidate pack governance.** Use negative tests and isolated synthetic fixtures until `D23-07` is accepted.

## 3. Build order

### Work package `I23-00` — Contract alignment

- Read the approved Increment-1 contract inventory and schemas.
- Produce a dependency matrix mapping every task output to one contract/version.
- Confirm evidence-set/profile/metadata/context manifest ownership.
- Stop on missing, duplicate or contradictory record ownership.

**Exit:** architecture/contract owner accepts the dependency matrix; no schema is invented locally.

### Work package `I23-01` — Runtime request and authorization

- Define Lakeflow job parameters with bundle-variable defaults where appropriate.
- Validate identifiers, JSON table allow-list, required policy versions and source/output separation.
- Register immutable work-package and authorization snapshots.
- Add idempotent state transition and optimistic concurrency handling.

**Exit:** unauthorized, placeholder, duplicate, malformed and cross-scope requests fail before source access.

### Work package `I23-02` — Metadata snapshot

- Implement the typed inventory adapter against Unity Catalog information schema.
- Add deterministic fallbacks for DDL/extended metadata where approved.
- Persist complete outcome coverage, query references and metadata snapshot fingerprints.
- Add incomplete-visibility and privilege-loss tests.

**Exit:** one authorized proof slice produces complete object/attribute outcomes or explicit failures; rerun is idempotent.

### Work package `I23-03` — Controlled profiling

- Implement policy-driven, template-only profiling.
- Enforce sampling, query, time, concurrency, masking, suppression and retention policies before write.
- Persist profile method, sample, approximation and policy provenance.
- Prove no prohibited values leak through Delta, logs, exceptions or MLflow traces.

**Exit:** all `D23-03`/`D23-04` policy cases and failure tests pass; accepted proof-slice thresholds pass.

### Work package `I23-04` — Supplied evidence

- Validate document/requirement entitlements and fingerprints.
- Normalize cited document claims and requirements with provenance classes retained.
- Treat instruction-like content as data.
- Add extraction failure, missing citation and prompt-injection tests.

**Exit:** every persisted extracted claim has an authorized source locator and typed provenance.

### Work package `I23-05` — Evidence readiness

- Validate contracts, references, authorization, coverage and policy outcomes.
- Persist the immutable evidence-set manifest and readiness summary.
- Transition only to `EVIDENCE_READY`; never call semantic capabilities.

**Exit:** all Increment-2 tests and accepted `D23-10` thresholds pass.

### Work package `I23-06` — Exact knowledge selection

- Extend the existing repository selector behind a runtime service.
- Add authorization, effective-time, scope, governed-content and fingerprint checks.
- Select exact modules/assets; prohibit latest/directory/candidate fallback.
- Implement revocation and dependency invalidation.

**Exit:** all negative selection tests pass. Positive path uses only an authorized isolated fixture or accepted `D23-07` pack.

### Work package `I23-07` — Evidence/decision retrieval

- Select exact task/object evidence and requirements.
- Filter approved decisions by engagement, scope, applicability, time and supersession.
- Detect cross-class and same-authority conflicts without flattening provenance.
- Enforce record/byte/token budgets before prompt rendering.

**Exit:** cross-engagement and stale inputs fail; conflicts and omissions are explicit.

### Work package `I23-08` — Context snapshot

- Build the deterministic minimal-context index and immutable manifest.
- Canonicalize references and configuration before hashing.
- Persist authorization/policy decisions, exclusions, contradictions and dependency edges.
- Validate and transition only to `CONTEXT_READY`.

**Exit:** identical immutable inputs are idempotent; changed/revoked dependencies produce a new or invalidated snapshot; `D23-11` thresholds pass.

## 4. Expected project placement

Use the project’s package and DAB conventions. Exact names may follow the approved Increment-1 inventory, but responsibilities should be separated as:

```text
resources/
  source_discovery.job.yml
src/agentic_data_modeler/
  control/
  source_adapters/
  evidence/
  context/
  persistence/
src/workflows/
  validate_scope.py
  register_work_package.py
  snapshot_source_metadata.py
  profile_source.py
  normalize_supplied_evidence.py
  verify_evidence_ready.py
  select_authorized_knowledge.py
  assemble_context_snapshot.py
  validate_context_ready.py
tests/
  unit/
  integration/
  security/
  fixtures/synthetic/
```

Do not interpret this layout as permission to duplicate contract validation across packages. Keep one contract-validation boundary owned by Increment 1.

## 5. Mandatory quality gates

- `databricks bundle validate` passes for each target.
- Per-run scope can be changed through job parameters without redeployment.
- Every task is idempotent and resumable from durable state.
- Source adapters are read-only and solution writers cannot modify source or governed knowledge.
- Contracts and referential integrity validate before readiness transitions.
- All source/evidence/context references are engagement- and scope-isolated.
- Candidate/unapproved knowledge fails closed.
- No prohibited raw value appears in output, logs, traces or exceptions.
- Failure injection covers lost privilege, timeout, retry, partial write, fingerprint mismatch, revocation and stale dependencies.
- The proof slice meets human-approved completeness, cost, latency, recovery and security thresholds.

## 6. Evidence Genie Code must return for review

For each work package provide:

- files changed and the contract/version implemented;
- test names and results, including negative and security cases;
- bundle validation output;
- example run request containing no secrets or real source values;
- task/run IDs and state-transition evidence;
- record counts, coverage and explicit failures;
- authorization/policy decisions referenced;
- MLflow/operational trace references with redaction verified;
- unresolved decisions or contract gaps; and
- a statement that no approval/runtime eligibility or governed knowledge was changed.

## 7. Stop conditions

Stop and return a blocking finding when:

- Claude’s Increment-1 contract and this specification conflict;
- a human decision in the register is required for the next action but remains open;
- completing a test would require weakening authorization, masking, retention or pack approval;
- metadata/profile/evidence coverage cannot be reconciled to the requested allow-list;
- an output would require semantic inference; or
- the builder would need to modify a governing document, knowledge pack or approval state.
