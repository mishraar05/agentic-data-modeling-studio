# ADR-006: Episodic memory is unrealized — system-of-record vs. memory, and the missing context/enrichment flows

**Status:** Proposed
**Date:** 2026-07-18
**Decision owner:** Solution owner (architecture)
**Reviewer:** Independent AI architecture review
**Amends:** [`ADR-004`](ADR-004-memory-taxonomy.md) (memory taxonomy)
**Related:** [`ADR-002`](ADR-002-proof-slice-minimal-scope.md) (proof slice), [`ADR-005`](ADR-005-architecture-review-findings.md) F3/F4 (working memory, retrieval), [`AGENT_SOLUTION_ARCHITECTURE.md`](../architecture/AGENT_SOLUTION_ARCHITECTURE.md) §4.1–§4.2, [`REQUIREMENTS_CHARTER.md`](../requirements/REQUIREMENTS_CHARTER.md) §7

## Context

ADR-004 names an "episodic memory" store (engagement decisions & runs). A review of the implementation shows that, as built, **the episodic memory does not exist as a functioning capability** — only its table contracts and DDL do — and **the flows that would make it memory (context assembly, decision capture, enrichment/feed-forward) are absent.**

### Evidence from the codebase

- **No context assembler exists.** A search for any context-assembly / envelope module returns nothing. The context assembler described in Architecture §4.1 and the Increment-3 spec is unimplemented.
- **Context snapshots are not assembled.** In `src/workflows/register_work_package.py` and `src/workflows/snapshot_source_metadata.py`, the field is hard-coded `"context_snapshot_id": None`. The only `context` references in the workflows are Databricks notebook plumbing, unrelated to the agent context envelope.
- **No code reads `review_decision` or `open_question`.** No runtime path recalls prior decisions into a later run. The only matches are the generic schema-builder utilities that emit DDL for every table.
- **No decision-capture path.** The review app (`src/apps/model_review/app.py`) is a stub, so no `review_decision` record is ever produced.
- **The one real "context" primitive is semantic selection only.** `knowledge/registry.py::select_approved_pack` performs fail-closed *pack selection*. That is pack-picking, not envelope assembly, and has no episodic dimension.

Net: what runs today is a linear, memoryless pipeline — register scope → snapshot metadata → select approved pack. There is no recall, no accumulation, no learning.

### The store is correctly *not* in the knowledge pack

Episodic records must not live in the knowledge pack. The pack is *semantic* memory: cross-engagement, immutable, approved. Episodic records are engagement-scoped, mutable, and append-only. Keeping them separate is required by engagement isolation (Charter §6). "Not in the pack" is correct by design; the gap is that the episodic store and its flows are unbuilt.

## Findings

### F1 — "Episodic memory" over-claims; most of the store is control/provenance data

ADR-004 files `review_decision`, `open_question`, `context_snapshot`, `solution_run`, `work_package`, and `artifact_version` under "episodic memory." But:

- `review_decision`'s primary role is **authorization/approval-state** (it gates `APPROVED`), which ADR-004 elsewhere classifies as **execution, not memory**. The same record does double duty.
- `review_decision` is a **human governance action recorded about the agent's output**, not the agent's own episodic experience; and it is retrieved (by design) via scope-filtered SQL, not memory-style relevance recall.
- `work_package`, `solution_run`, `context_snapshot`, `artifact_version` are **run identifiers, provenance, and lineage bookkeeping** — not memory by any definition.

When a taxonomy must call `artifact_version` "episodic memory," the label has been stretched to mean "every durable engagement-scoped record." That is a data tier, not a cognitive faculty. **Memory is the read-path/projection over these records, not the tables themselves.**

### F2 — The memory mechanism is missing (the decisive finding)

Even granting the memory framing, the mechanism that would make the store *behave* as memory is absent on all three edges:

1. **Context assembly (read path)** — assemble a bounded envelope per task from the semantic pack slice + prior decisions/open-questions for this engagement+object scope + evidence + requirements. **Not built** (`context_snapshot_id = None`; no assembler module).
2. **Decision capture (write path)** — review action → `review_decision` / `open_question`. **Not built** (review app is a stub).
3. **Enrichment / feed-forward** — prior decisions re-entering the next run, closing open questions, and the episodic→semantic consolidation gate. **Not built.**

Without all three, "episodic memory" names an empty table.

### F3 — A core value proposition is unimplemented

Two headline charter outcomes depend entirely on this loop and are currently unbuilt:

- "prior approved decisions become durable input to the next run" (SDD design Phases 0/8);
- "reduce reviewer override rate through learning from approved decisions" (Charter §7).

The capability that would make the system *improve as humans use it* — its main differentiator over a one-shot LLM call — does not exist, not even in skeleton.

## Decision

1. **Reframe the axis.** Model the durable engagement tier as an **Engagement System of Record** (append-only decision ledger + provenance/lineage) with an **Engagement Memory** *service* — a retrieval projection — layered on top. Memory is the read-path, not the tables. ADR-004's taxonomy is retained as a **placement and isolation** tool, but the storage tables are no longer asserted to *be* cognitive memory.
2. **Reclassify the records** (below) into control/provenance vs. memory-feeding, so each gets the right treatment (audit/completeness vs. relevance/recency, per ADR-005 F4).
3. **Build the minimal memory loop** as the way to make episodic memory real, scoped to the ADR-002 proof slice — not a full memory subsystem.
4. **Fix the diagram.** The SDD flow canvas must show the read-back into Phase 0 and the write from Phase 8 marked *designed, not built*, rather than implying the store is wired in.

### Record reclassification

| Record | Primary role | Feeds memory (read-path)? |
|---|---|---|
| `review_decision` | Control — approval authority + audit | Yes — "already decided about this object" |
| `open_question` | Control/workflow — unresolved-item ledger | Yes — reopen/close before re-analysis |
| `context_snapshot` | Provenance — reproducibility | No (it *is* the assembled envelope's record) |
| `solution_run` | Provenance — run identity | No |
| `work_package` | Control — scope identity | No |
| `artifact_version` | Provenance — versioning | No |

Only `review_decision` and `open_question` feed the memory projection; the rest are system-of-record/provenance and should stop being labelled "episodic memory."

### Minimal memory loop to build (proof-slice scope)

- **A1 — Context-assembly function.** Given engagement/LOB/domain/object scope, assemble the envelope: the selected pack slice (existing `select_approved_pack`) + prior `review_decision`/`open_question` for that scope + evidence + requirements, and persist a real `context_snapshot` (replace `context_snapshot_id = None`).
- **A2 — Decision-capture path.** Wire the review app to write `review_decision`/`open_question` records (control-plane authority), completing the write edge.
- **A3 — Feed-forward read-back.** Phase 0 of the next run reads A2's records via A1 into the envelope; open questions gate re-analysis.
- **A4 (deferred).** Relevance/recency ranking and episodic→semantic consolidation — only after A1–A3 demonstrably close the loop on the proof slice.

## Consequences

- Episodic "memory" becomes real only when A1–A3 exist; until then it is documented as *unrealized* rather than implied to work.
- The retrieval-policy gap (ADR-005 F4) and the control-vs-recall split (ADR-005/this ADR) are resolved by separating the ledger (audit/completeness) from the memory projection (relevance/recency).
- The agent **reads** the memory projection and **never writes** decisions; decisions are human-authored control records. This invariant is now explicit and is easier to enforce once the two roles are named separately.
- No Charter deliverable, `approval_state`, or `runtime_eligible` changes. This is an architecture correction plus a build item.
- Reinforces ADR-002/ADR-005: the near-term priority is proving one end-to-end loop, not adding design surface.

## Charter alignment

Applies Charter §7 (learning from approved decisions; reproducibility) and §6 (engagement isolation). It amends the framing of ADR-004 §4.2 but does not change the goal, deliverables, or principles; a material change to those still requires an explicit owner decision.
