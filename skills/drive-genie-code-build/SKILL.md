---
name: drive-genie-code-build
description: >-
  Drive the Genie Code builder to construct the Agentic Data Modeling Studio one
  increment at a time. Use when someone asks to actually build or generate the
  solution code through Genie Code — select the correct build Skill for the
  target increment, enforce the roadmap's prerequisite gates, prepare the Genie
  Code handoff, run it in the right build mode, then validate and gate the build
  evidence it returns. This is a build-orchestration Skill in the authoring
  plane: it never writes solution code itself, never runs an engagement, and
  never changes contracts, governing documents, decisions, or knowledge-pack
  approval.
---

<!--
Packaging note: only `name` and `description` are portable top-level frontmatter
keys. Version, owner, and status live in the "Status and authority" section so
this file validates against the Agent Skills format.
-->

# Drive Genie Code Build

## Status and authority

Version: `0.1.0-DRAFT`
Owner: architecture owner (`TBD`)
Status: `READY_FOR_USE_AS_BUILD_ORCHESTRATOR`

This Skill is the **conductor** for the solution build. It does not itself
generate code — **Genie Code** does. It selects the correct per-increment build
Skill, hands Genie Code a bounded, authorized build request, and validates what
comes back. Claude/Codex may drive this orchestration; the actual code
generation happens wherever Genie Code runs (Databricks). If no Genie Code
builder is available in the current environment, prepare the handoff and stop —
do not hand-write the producer code as a substitute.

Apply authority in this order; stop on conflict and never repair a
higher-authority artifact from this Skill:

1. Requirements Charter.
2. Approved Increment-1 contracts and validation behavior.
3. Agent Solution Architecture and accepted ADRs.
4. The target increment's implementation specification(s).
5. The Genie Code build handoff and accepted human decisions.
6. The selected build Skill.
7. This Skill.

## Build-Skill roadmap it drives

| # | Increment | Build Skill | Prerequisite gate |
|---|---|---|---|
| 1 | Increment 1 — contracts | `author-source-discovery-contracts` | governing docs readable and consistent |
| 2 | Increment 2-3 — foundation | `build-source-discovery-foundation` | Increment-1 contracts approved |
| 3 | Increment 4 — harness + SDD agent | `build-sdd-agent-harness` *(planned)* | foundation `VERIFIED`; a runtime-eligible pack or authorized fixture |
| 4 | Increment 5-6 — review + handoff | `build-sdd-review-and-handoff` *(planned)* | harness `VERIFIED` |
| 5 | Cross-cutting — deploy | `validate-and-deploy-sdd-solution` *(planned)* | the increment(s) being deployed are `VERIFIED` |

Runtime reasoning skills (`SA1/SA2/SA3`, `X1/X2/X3`, `CR1`) are **not** driven
here as standalone builds; they are constructed inside `build-sdd-agent-harness`.
Operating the deployed solution is a **different** future Skill
(`run-sdd-work-package`), never this one.

## Trigger and non-trigger

**Trigger** when the request is to *build/generate the solution code through
Genie Code* for a named increment or work-package range, and the selected build
Skill and its governing specs exist.

**Do NOT trigger** when:

- the request is to *author or revise a build Skill's specification* (edit that
  Skill directly, not this one);
- the request is to run the deployed solution or a work package
  (`run-sdd-work-package`);
- the request is to make a human decision, approve a pack, or change a governing
  document.

## Preconditions

1. Read `AGENTS.md`, the Charter, the Agent Solution Architecture, and the target
   increment's implementation spec(s) completely.
2. Confirm the **target increment** and resolve its build Skill from the roadmap.
3. Confirm the **prerequisite gate** for that increment is satisfied. If it is
   not (e.g., Increment-1 contracts are not approved before the foundation),
   report the gap and stop — do not let Genie Code skip the gate.
4. Read the decision register. An open positive-path decision permits only
   negative-path or isolated synthetic development; it never permits a live
   positive build.
5. Confirm a Genie Code builder is available for this environment. If not,
   assemble the handoff (below) and stop at "ready to build."

## Orchestration method

### 1. Select and bound the work

- Pick exactly one build Skill for the target increment.
- Read that Skill and its bundled resources (its build contract, evaluation
  matrix, and handoff template).
- Set the **build mode** the target Skill defines (for the foundation Skill:
  `ALIGNMENT_ONLY`, `PHASE_A`, `PHASE_B`, or `FULL_FOUNDATION`).
- List the exact work packages to be built in this run.

### 2. Assemble the Genie Code handoff

- Point Genie Code at: the selected `SKILL.md` and its resources; the governing
  docs in authority order; the approved contract set and its version; and the
  accepted human decisions relevant to the work packages.
- State the build mode, the in-scope work packages, the file boundaries, and the
  quality gates the Skill requires.
- Restate the Skill's prohibitions and stop conditions in the request so the
  builder cannot silently weaken a gate.
- Include no credential, token, personal datum, or raw source value.

### 3. Run Genie Code

- Hand the bounded request to Genie Code and let it generate the producer code,
  tests, and resources within the declared file boundaries.
- Do not hand-author the producer code here; if the builder is unavailable or
  errors, record that and stop rather than substituting.

### 4. Validate the returned evidence

- Require one completed builder-handoff record for the run.
- Validate it with the target Skill's handoff validator, then run the repository
  regression suite and `databricks bundle validate` for the selected target.
- Confirm every in-scope work package is `VERIFIED` with cited contract
  versions, files, and tests — not merely `BUILT`.
- Confirm negative and security cases pass, and that the handoff attests no
  governing document, approval state, or `runtime_eligible` value changed.

### 5. Gate and progress

- Mark the increment built only when all its work packages are `VERIFIED` and all
  validations pass.
- On any blocking finding, open positive-path decision, or governance change,
  record it and stop; do not advance to the next increment.
- When an increment passes, re-check the next increment's prerequisite gate
  before driving its build.

## Prohibitions

Do not:

- write, repair, or "finish" solution producer code, contracts, adapters, or
  tests yourself — that is Genie Code's output;
- let Genie Code skip a prerequisite gate, invent or edit a contract, or build a
  positive path against a candidate or non-runtime-eligible pack;
- modify the Charter, architecture, decision register, ADRs, or any pack;
- alter `approval_state` or `runtime_eligible`, or mark an artifact approved;
- accept a build as complete from artifact counts or unit tests alone, or without
  a validated handoff;
- pass or persist prohibited raw values or credentials in the handoff.

## Stop conditions

Stop and report when:

- the target increment's prerequisite gate is not satisfied;
- a required positive-path human decision remains open;
- no Genie Code builder is available (stop at "handoff ready");
- the returned handoff fails validation, regression, or bundle validation;
- any work package cannot reach `VERIFIED` without weakening a security, privacy,
  or governance rule; or
- the build would require changing a higher-authority artifact.

## Completion

A driven build run is complete only when:

- every in-scope work package is `VERIFIED` in a validated builder-handoff;
- regression and `databricks bundle validate` pass for the selected target;
- the run record names the build Skill, build mode, work packages, evidence
  references, validator result, and the go/no-go decision for the next increment;
  and
- the handoff attests that no governing document, approval state, or runtime
  eligibility was changed.

Producing code is not the finish line; a validated, gate-respecting handoff is.
