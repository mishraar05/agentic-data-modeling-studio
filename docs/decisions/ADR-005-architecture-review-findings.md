# ADR-005: Architecture review findings — multi-agent scope, memory, and tools

**Status:** Proposed
**Date:** 2026-07-18
**Decision owner:** Solution owner (architecture)
**Reviewer:** Independent architecture review
**Scope reviewed:** [`AGENT_SOLUTION_ARCHITECTURE.md`](../architecture/AGENT_SOLUTION_ARCHITECTURE.md), [`SOURCE_DATA_DICTIONARY_AGENT_DESIGN.md`](../architecture/source-data-dictionary/SOURCE_DATA_DICTIONARY_AGENT_DESIGN.md), [`ADR-004`](ADR-004-memory-taxonomy.md), [`SKILL_MAP.md`](../architecture/SKILL_MAP.md)
**Related:** [`ADR-002`](ADR-002-proof-slice-minimal-scope.md) (scope), [`REQUIREMENTS_CHARTER.md`](../requirements/REQUIREMENTS_CHARTER.md) §7 (success measures)

## Context

The Source Data Dictionary (SDD) agent architecture was reviewed critically on three questions: is there scope for a multi-agent system; is memory properly architected; are tools properly architected.

Overall finding: **the design thinking is strong and disciplined — materially stronger than the implementation.** The multi-agent restraint is correct, the memory model is better-specified than most production systems, and the tool posture is security-sound. The problem is not design quality; it is that a large, elegant design sits on **zero empirical validation** (no `runtime_eligible` pack, no written contracts, no profiling tool, no unseen proof slice). The design's own open-dependencies section states the agent cannot execute its positive semantic path today. This is the same root cause as the over-engineering finding in ADR-002: effort has gone into designing and documenting the platform rather than proving the core capability once.

This ADR records the specific gaps as tracked, actionable items. It does not change any Charter deliverable.

## Findings

### F1 — Multi-agent scope is correct; critic independence is the real weak point (HIGH)

The architecture correctly uses one custom harness with specialist capabilities (§2) rather than a fleet of deployed agents, with a clean promotion rule (separate agent only for a different context boundary, tool authority, lifecycle, scaling profile, or eval regime). The authoring plane is already split outside the runtime harness, and the Supervisor is correctly deferred. No premature multi-agent sprawl.

However, the **Model Critic (CR1)** is the one capability that genuinely earns separation, and it is kept in-harness. Every semantic-quality claim in Charter §7 rests on independent evaluation. The design acknowledges that a critic sharing the producer's model and context envelope inherits its blind spots and that agreement is "correlated, not independent," but still keeps the critic as a skill+phase inside the same harness. Rephrasing a rubric does not create independence. This is the highest-leverage architectural risk: the thing that underpins every quality claim is only partially independent.

### F2 — Inter-capability orchestration is undefined (MEDIUM)

Seven capabilities exchange typed contracts and are permitted to "debate or critique one another" (§2), but there is no state machine for how work and rework flow *across* the seven — call order, handoff, loop termination, and back-pressure when a downstream capability (e.g. Silver) rejects an upstream slice (e.g. SDD). The solution avoids *deployed* multi-agent cost but still carries multi-agent *coordination* cost, currently undesigned. The per-agent phase list (SDD Phases 0–9) exists; the cross-agent workflow does not.

### F3 — Working / short-term memory is under-architected (MEDIUM/HIGH at scale)

`ADR-004` / §4.2 defines an excellent three-store durable-memory taxonomy — semantic (packs), episodic (decisions/runs), procedural (skills), plus execution declared not-memory — with mechanical placement, engagement isolation, and a human-gated episodic→semantic consolidation gate. This is the strongest part of the architecture.

But the taxonomy covers only *durable* memory. Run-scoped **working memory** — how the evolving draft and intermediate evidence are held, compacted-with-provenance, and passed across a 9-phase run when a source object has hundreds of columns — is mentioned only as "run-scoped" and "not durable." This is precisely where context-window pressure and resumability bite, and it is the real scaling risk. The harness lists "checkpoints" but no working-memory compaction design.

### F4 — Retrieval within a memory store is hand-waved (MEDIUM)

Semantic memory is selected by exact pack version (correct for governance) but packs can be large, and "the context assembler selects the smallest sufficient subset" is asserted, not designed. Episodic memory is append-only with no relevance/recency policy, so "prior approved decisions for this object" can grow unbounded into the context envelope. No retrieval or ranking mechanism is specified beyond the fail-closed version selector.

### F5 — Tools are the least-specified layer, and the load-bearing one (HIGH)

The tool *posture* is right: read-only source tools separated from artifact-write tools, tool-permission-as-middleware (not in prompts), args constrained to engagement scope, least privilege (no production deploy, migration, credential, or unrestricted SQL authority), and `ai_extract`/`ai_classify`/Genie treated as bounded helpers behind adapters. `SKILL_MAP` §1 cleanly separates tool vs skill vs validator.

But, against a project that insists on typed contracts everywhere:

- **No tool contracts exist.** The tool surface is named only abstractly (`select_approved_pack`, "allow-listed read tool," "profile store") with no signatures, arg-scoping mechanism, or I/O schema, despite §6 requiring a "scoped tool registry with policy middleware."
- **The most value-critical tool, profiling, is neither built nor contracted**, and the SDD design admits its absence "materially weakens exactly the inferences the charter values most."
- **Tool-failure semantics are undefined** (partial failure, timeout, degraded-mode declaration) beyond global time/cost/token/recursion limits.

### F6 — Prompt-injection defense is asserted, not designed (MEDIUM, security)

Guardrails state untrusted documents are "scanned for instruction-like content and treated as data." The intent is right, but evidence adapters ingesting third-party dictionaries and report definitions are a real injection surface, and "scanning" is a weak control to assert without a specified mechanism, isolation boundary, or failure behavior.

## Decision / recommended actions

Adopt the following as tracked work items, prioritized. Items are sequenced to fix the highest-risk, most load-bearing gaps before adding further design surface, consistent with ADR-002.

| ID | Action | Finding | Priority |
|---|---|---|---|
| A1 | Make the critic genuinely independent: separate context assembly, a different approved model, and a defined adversarial contract; decide explicitly whether it becomes a separate agent. Treat producer/critic agreement as correlated confirmation until independence is demonstrated. | F1 | HIGH |
| A2 | Write the tool/registry contracts, starting with the profiling tool and `select_approved_pack`: signatures, arg-scoping, I/O schema, and per-tool failure/degraded-mode semantics. | F5 | HIGH |
| A3 | Design run-scoped working memory: compaction-with-provenance across phases, checkpoint contents, and resumability for wide source objects. | F3 | HIGH |
| A4 | Specify retrieval within stores: smallest-sufficient selection inside a pack, and a relevance/recency policy for episodic decisions entering the context envelope. | F4 | MEDIUM |
| A5 | Design the cross-capability orchestration/state machine: call order, handoff, rework loops, termination, and back-pressure across the seven capabilities. | F2 | MEDIUM |
| A6 | Replace asserted injection "scanning" with a specified defense: isolation boundary for untrusted document content, mechanism, and failure behavior. | F6 | MEDIUM |
| A7 | Prove the core once: one `runtime_eligible` pack slice + ~5 real tables through the full SDD phase flow end-to-end, before adding further design surface. | all | HIGH |

## Consequences

- A1, A2, A3, and A7 are the near-term architecture priorities. A7 is the validation that converts "sound on paper" into evidence and should not be deferred behind more design.
- None of these findings requires a Charter change; they are architecture refinements plus one validation milestone.
- The design's strengths (multi-agent restraint, memory taxonomy, tool posture, LLM/deterministic split) are retained; this ADR sharpens the three thinnest layers and forces empirical validation.
- If A7 is repeatedly deferred, the gap between design maturity and demonstrated capability will keep widening — the exact pattern ADR-002 and the Charter anti-drift gate (§8) exist to stop.

## Charter alignment

This review applies Charter §7 (semantic quality proven only on unseen, independently labelled cases — the basis for F1) and §8 question 5 (skill vs tool vs validator vs context — the basis for F5). It does not alter the goal, deliverables, or principles; a material change to those still requires an explicit owner decision.
