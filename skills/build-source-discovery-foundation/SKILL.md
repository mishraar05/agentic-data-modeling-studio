---
name: build-source-discovery-foundation
description: >-
  Build or revise the deterministic Increment 2-3 Source Discovery foundation
  for the Agentic Data Modeling Studio: DAB/Lakeflow job parameters and tasks,
  work-package authorization, metadata inventory, controlled profiling,
  supplied-evidence normalization, Delta persistence, exact governed-context
  selection, immutable context snapshots, and their security, idempotency and
  readiness tests. Use when Genie Code or an engineer must implement I23-00
  through I23-08 after the Increment-1 contract gate. Do not use for runtime
  source interpretation, SDD semantic generation, solution execution, contract
  invention, knowledge approval, or Silver/Gold/STTM work.
---

# Build Source Discovery Foundation

## Status and authority

Version: `0.2.0-DRAFT`  
Owner: architecture owner (`TBD`)  
Status: `READY_FOR_BUILDER_USE_AFTER_CONTRACT_GATE`

Build deterministic solution components that move one authorized work package:

```text
VALIDATED -> METADATA_READY -> PROFILE_READY -> EVIDENCE_READY -> CONTEXT_READY
```

Operate in the authoring plane. Never run an engagement, infer source meaning,
approve an artifact, or change knowledge-pack governance.

Apply authority in this order:

1. Requirements Charter.
2. Approved Increment-1 contracts and validation behavior.
3. Agent Solution Architecture and accepted ADRs.
4. Increment-2 and Increment-3 implementation specifications.
5. Genie Code build handoff and accepted human decisions.
6. This Skill.

Stop on conflict; never repair a higher-authority artifact from this Skill.

## Load the right resources

Always read `references/build-contract.md`. It defines prerequisites, work-package
ownership, file boundaries and decision gates.

Read `references/evaluation-matrix.md` before implementing tests or claiming a
work package is verified.

Copy `assets/builder-handoff.template.yml` for the build evidence returned by
Genie Code. Validate the completed handoff with:

```text
python scripts/validate_builder_handoff.py <handoff.yml>
```

Do not copy detailed rules from these resources into new local specifications.

## Preconditions

1. Read `AGENTS.md`, the Charter and controlling architecture completely.
2. Verify the governing files are readable, complete and internally consistent.
3. Resolve the exact Increment-1 contract inventory and production schemas.
4. Produce the `I23-00` dependency matrix mapping every task output to one
   contract and version.
5. Confirm the requested build mode:
   - `ALIGNMENT_ONLY`: dependency analysis; no producer code.
   - `PHASE_A`: `I23-01..05`, ending at `EVIDENCE_READY`.
   - `PHASE_B`: `I23-06..08`, consuming authorized `EVIDENCE_READY` fixtures.
   - `FULL_FOUNDATION`: Phase A followed by Phase B.
6. Read the decision register. An open decision permits negative-path or isolated
   synthetic development only; it never permits a live positive path.

Production contracts are currently a hard execution gate. If `contracts/`
contains no approved schemas, complete `I23-00`, report the gap and stop before
creating producers or parallel schemas.

## Build method

### 1. Align contracts and task ownership

- Map all outputs and references for `I23-00..08` to the approved contract set.
- Distinguish authoring order from runtime instance references.
- Reuse the single Increment-1 validation boundary.
- Reject missing, ambiguous, duplicate or locally invented record ownership.

### 2. Establish the bounded DAB job

- Create a dedicated `source_discovery` Lakeflow job.
- Use job parameters for per-run scope and bundle variables only for
  environment/deployment defaults.
- Keep credentials, tokens, personal data and raw source values out of both.
- Separate read-only source authority, solution-owned writes and human approval
  transitions.
- Use thin workflow entry points; keep business logic in package modules.

### 3. Build Phase A source onboarding

- Implement authorization before any source read.
- Snapshot complete allow-listed metadata with explicit failure outcomes.
- Run only reviewed, policy-bound profiling templates; never let an adapter
  upgrade its run mode.
- Suppress prohibited values before persistence, logging or tracing.
- Normalize supplied documents and requirements with entitlements, fingerprints,
  typed provenance and durable source locators.
- Advance to `EVIDENCE_READY` only after contract, reference, authorization,
  coverage and policy validation meets accepted thresholds.

### 4. Build Phase B governed context assembly

- Require an authorized `EVIDENCE_READY` work package.
- Select an exact approved, runtime-eligible pack and exact modules/assets. Never
  use latest, nearest, directory or candidate fallback.
- Preserve all provenance classes; never let a decision erase contrary source
  facts.
- Apply engagement, scope, effective-time, supersession, authorization and
  fingerprint filters deterministically.
- Enforce record/byte/token budgets before rendering; stop rather than silently
  omit a required blocking item.
- Persist an immutable context manifest/index with canonicalization version,
  content fingerprint and queryable dependency invalidation.
- Advance to `CONTEXT_READY` only after accepted thresholds pass.

### 5. Make every task durable and observable

- Derive idempotency keys from pinned scope, inputs, policy, contract, adapter and
  task versions.
- Return existing immutable outputs for identical keys; create new versions when
  dependencies change.
- Stage writes and commit only contract-valid complete records.
- Capture MLflow/Delta operational evidence without prohibited values.
- Add bounded retries, checkpoints, optimistic concurrency and failure injection.

### 6. Return reviewable build evidence

- Complete one handoff record for each build attempt.
- Record every work package `NOT_STARTED`, `BLOCKED`, `BUILT` or `VERIFIED`.
- Cite contract versions, files and tests for every verified work package.
- Record open decisions and blocking findings without weakening gates.
- Attest that governing documents, approval state and runtime eligibility were
  not changed.
- Run the handoff validator and the repository regression suite.

## Prohibitions

Do not:

- author or repair Increment-1 contracts inside producer code;
- infer source semantics, create dictionary definitions, or invoke modeling
  Skills;
- modify the Requirements Charter, architecture, decision register or ADRs;
- alter `approval_state`, `runtime_eligible`, pack contents or source evidence;
- execute DDL/DML against source systems or allow model-generated arbitrary SQL;
- treat document claims as source facts;
- persist prohibited raw values or security credentials;
- declare readiness from artifact counts or unit tests alone.

## Stop conditions

Stop and return a blocking handoff when:

- the contract gate fails or task ownership is ambiguous;
- a required positive-path human decision remains open;
- requested source access or policy authority is absent;
- evidence coverage cannot reconcile to the allow-list;
- knowledge selection is ambiguous, candidate-only, expired or unauthorized;
- a required item cannot fit within an authorized context budget;
- the requested output requires semantic inference or a downstream SDD/Silver/
  Gold/STTM capability; or
- validation would require weakening a security, privacy or governance rule.

## Completion

Do not call the foundation complete until:

- all `I23-00..08` entries are `VERIFIED` in a valid handoff;
- DAB validation passes for the selected target;
- unit, integration, security, idempotency and failure-injection evidence exists;
- an authorized proof slice meets human-approved Phase A and Phase B thresholds;
- no prohibited values appear in tables, logs, traces or exceptions; and
- architecture/contract reviewers accept the build evidence.

Synthetic positive fixtures prove implementation paths, not production readiness.

## Changelog

- `0.2.0-DRAFT`: consolidated the overlapping Increment-2 and Increment-3
  authoring drafts; added progressive references, a governed builder-handoff
  template, deterministic handoff validation and explicit build modes.
- `0.1.0-DRAFT`: initial combined Increment 2-3 build playbook.
