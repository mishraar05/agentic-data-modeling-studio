# ADR-004: Memory taxonomy — episodic decisions, semantic knowledge, procedural skills

**Status:** Accepted  
**Date:** 2026-07-16  
**Decision owner:** Solution owner (architecture)

## Context

The solution already separates three kinds of durable state, but never names them as a memory model. [`AGENT_SOLUTION_ARCHITECTURE.md`](../architecture/AGENT_SOLUTION_ARCHITECTURE.md) §4.1 defines a governed knowledge layer and states that "durable memory consists only of versioned evidence, artifacts, and approved decisions"; §7 forbids LOB/domain/engagement facts inside a `SKILL.md`; [`SKILL_MAP.md`](../architecture/SKILL_MAP.md) §1 assigns every work item a single home (code, tool, validator, governed context, or skill); and the [Increment 2–3 decision register](../architecture/source-data-dictionary/INCREMENT_2_3_HUMAN_DECISION_REGISTER.md) treats engagement decisions (e.g. `D23-01`) as run-scoped authority.

Because the distinction is implied across four documents rather than named in one, the same placement question keeps recurring — for example, where the `D23-01` proof-slice source/table allow-list belongs, and whether a human-in-the-loop questionnaire's answers may be stored "as a setting" inside a skill. Naming the memory model makes these placement decisions mechanical and prevents engagement data from leaking into reusable knowledge.

This is an architecture decision only. It does not change any Requirements Charter deliverable, `approval_state`, or `runtime_eligible`.

## Decision

Adopt a three-store memory taxonomy, mapped to the cognitive memory systems. Every persistent thing the solution keeps classifies into exactly one store; deterministic enforcement is execution, not memory.

| Store | Memory type | Holds | Scope | Lifecycle |
|---|---|---|---|---|
| Governed knowledge layer (Architecture §4.1) | **Semantic** | General domain meaning: glossary, code sets, LOB/domain modules, modeling standards, approved reference models | Cross-engagement, reusable | Versioned pack; `CANDIDATE` → `APPROVED`; immutable versions |
| Engagement decision & run stores | **Episodic** | Events bound to engagement/run/time: decision records (e.g. the `D23-01` allow-list), `review_decision`, `open_question`, `context_snapshot`, `solution_run`, `work_package`, `artifact_version` | Engagement- and scope-isolated | Append-only / versioned; never auto-promoted |
| Skills (`SKILL.md`, Architecture §7) | **Procedural** | How to perform a bounded, evaluable reasoning task | Reusable playbook | Versioned; gated on unseen evaluation cases |

Deterministic scope/authorization gates (`00_validate_scope.py`, tool-permission middleware, approval-state enforcement) are **execution, not memory**, and remain in code per `SKILL_MAP.md` §1.

### Placement rule (normative)

- A general truth about the domain → **semantic** (knowledge pack).
- A fact or decision true only for one engagement/run → **episodic** (decision/run store).
- A reusable procedure → **procedural** (skill).
- A safety invariant or gate → **deterministic code**, not memory.

Domain content never enters a skill; engagement data never enters the knowledge layer.

### Consolidation gate (episodic → semantic)

Repeated approved decisions may reveal a generalizable pattern worth adding to reusable knowledge (Charter §7 — reducing reviewer overrides through learning from approved decisions). Promotion from episodic to semantic memory is a **governed, human-reviewed authoring act** performed on the knowledge-pack maintainer plane via [`build-governed-knowledge-pack`](../../skills/build-governed-knowledge-pack/SKILL.md). It must strip engagement-specific facts, retain only the generalizable pattern with authoritative provenance, and pass the pack's review and evaluation gates. It is never an automatic or silent write, and it may not set `APPROVED` or `runtime_eligible`. Engagement isolation (Charter §6) bounds it: one engagement's episodic memory must never enter another's context except through approved semantic knowledge.

## Worked example — `D23-01` proof-slice allow-list

| Element | Store | Where it lives |
|---|---|---|
| The questionnaire that elicits the scope (fields, options, impact framing) | Procedural | A skill — an `X2 formulate-clarification-question` specialization |
| The chosen source system, catalog, schema, connected Policy/Claims tables, LOB/domain, in/out-of-scope | Episodic | The `D23-01` decision record in the governed decision store |
| The domain meaning the questionnaire references (Personal Auto concepts, code sets) | Semantic | The governed knowledge pack |
| The fail-closed check that rejects a run not matching an accepted allow-list | Execution | `00_validate_scope.py` + `I23-01` authorization |

The allow-list values must **not** be stored in the skill. The skill is the procedure; the answer is an episode; the enforcement is code.

## Consequences

- Architecture §4.1's "durable memory" is named as **episodic** (decisions/runs) plus **semantic** (knowledge layer); §7's skills are named as **procedural**. A concise §4.2 in the architecture document records the taxonomy and points here.
- No Charter deliverable, `approval_state`, or `runtime_eligible` changes.
- Any future durable store must classify into exactly one memory type, or declare itself execution rather than memory.
- The episodic → semantic arrow always passes through review; the reviewer-learning loop (Charter §7) and `build-governed-knowledge-pack` enforce it.
- The controlling architecture has since been restored and verified complete. That repair is recorded as accepted decision `D23-13`; it does not change this memory taxonomy.

## Relationships

- Extends `AGENT_SOLUTION_ARCHITECTURE.md` §4.1 (governed knowledge layer) and §7 (judicious use of `SKILL.md`).
- Consistent with `SKILL_MAP.md` §1 (single-home-for-each-work-item table) and §4 (anti-sprawl register).
- Informs the intake design for engagement decisions in the [Increment 2–3 decision register](../architecture/source-data-dictionary/INCREMENT_2_3_HUMAN_DECISION_REGISTER.md), starting with `D23-01`.
